import os
from typing import Any, Callable, Optional, TypeVar, Dict

from numpy import var
from backend import NGSBackend
from benchling import exceptions
from benchling.exceptions import no_assay_run_found_for_ngs_run_error
from benchling.schemas import FwdRevClonePrimerInfo, FwdRevPrimerInfo, NGSPPPlate, PCRPlateMatch, SamplePrimerInfo
from benchling.utils import get_field_id_from_custom_entity, to_string, to_string_list
from schemas import Analysis, ClonePoolPrimerInfo, ClonePrimerInfo, MutationPurityAnalysis, PrimerInfo, MutationInfo
from schemas import PurityAnalysis, RepertoireAnalysis, NGSRunInfo, BenchlingEntity, User
from caching import CacheManager
from benchling_api_client.v2.stable.models.plate import Plate
from benchling_api_client.v2.stable.models.well import Well
from benchling_api_client.v2.stable.models.fields import Fields
from benchling_api_client.v2.stable.models.field import Field
from benchling_api_client.v2.stable.models.blob import Blob
from benchling_api_client.v2.stable.models.assay_run import AssayRun
from benchling_api_client.v2.stable.models.custom_entity import CustomEntity
from benchling_api_client.v2.stable.models.dna_sequence import DnaSequence
from benchling_api_client.v2.stable.models.simple_field_definition import SimpleFieldDefinition
from benchling_sdk.models import AutomationOutputProcessorCreate, AutomationOutputProcessor
from benchling_sdk.services.v2.stable.lab_automation_service import LabAutomationService
from benchling_sdk.services.v2.stable.blob_service import BlobService
from benchling_api_client.v2.stable.models.dna_oligo import DnaOligo
import json
import time
import re
import pandas as pd
import tempfile
from pydantic.json import pydantic_encoder

class NGSBenchlingBackend(NGSBackend):

    def __init__(self, cache_manager: CacheManager):
        super().__init__()
        self.cache_manager = cache_manager

    def run_and_measure_time(self, message, method):
        print(message)
        start = time.time()
        result = method()
        stop = time.time()
        elapsed = stop - start
        print("===DONE [" + str(elapsed) + "sec]===")
        return result

    def get_clone_pool_primer_info(self, pp_id: str, ngs_run_id: str) -> list[ClonePoolPrimerInfo]:
        self.cache_manager.reset()
        pcr_plates = self.get_pcr_plates(pp_id=pp_id)
        amplicon_value = self.choose_amplicon_value_for_ngs_run(ngs_run_id=ngs_run_id)
        primers_forward = []
        primers_reverse = []
        oligos: list[ClonePoolPrimerInfo] = []
        for plate in pcr_plates:
            container = self.cache_manager.get_cached_or_execute(
                method_name='benchling.containers.get_by_id',
                args={'container_id': plate.plate_id},
                callable=self.benchling.containers.get_by_id
            )
            print("PCR PLATE ID IS: ")
            print(str(plate.plate_id))
            clone_pool = container.contents[0].entity
            primer_forward = container.fields['Primer - Forward']
            primer_reverse = container.fields['Primer - Reverse']
            primers_forward.append(primer_forward)
            primers_reverse.append(primer_reverse)

            if type(primer_forward.value) is str and type(primer_reverse.value) is str:
                oligo_forward_fields = self.cache_manager.get_cached_or_execute(
                    method_name='benchling.dna_oligos.get_by_id',
                    args={'oligo_id': str(primer_forward.value)},
                    callable=self.benchling.dna_oligos.get_by_id
                ).fields
                oligo_reverse_fields = self.cache_manager.get_cached_or_execute(
                    method_name='benchling.dna_oligos.get_by_id',
                    args={'oligo_id': str(primer_reverse.value)},
                    callable=self.benchling.dna_oligos.get_by_id
                ).fields

                rev = self.fields_to_primer_info(oligo_reverse_fields)
                fwd = self.fields_to_primer_info(oligo_forward_fields)
                clone_pool_name = ''
                if type(clone_pool) is CustomEntity:
                    clone_pool_name = clone_pool.name

                info: ClonePoolPrimerInfo = ClonePoolPrimerInfo(
                    CLP=clone_pool_name,
                    fwdIsSymmetric=fwd.isSymetric,
                    fwdIsUnsymetric=fwd.isUnsymetric,
                    fwdRobustness=fwd.robustness,
                    fwdDirection=fwd.direction,
                    fwdPrimer=fwd.primer,
                    fwdPrimerType=fwd.primerType,
                    fwdPrimerSequence=fwd.primerSequence,
                    fwdBcSequence=fwd.bcSequence,
                    revIsSymetric=rev.isSymetric,
                    revIsUnsymetric=rev.isUnsymetric,
                    revRobustness=rev.robustness,
                    revDirection=rev.direction,
                    revPrimer=rev.primer,
                    revPrimerType=rev.primerType,
                    revPrimerSequence=rev.primerSequence,
                    revBcSequence=rev.bcSequence,
                    pcrPlate=plate.pcr_plate,
                    amplicon=amplicon_value
                )
                oligos.append(info)

        return oligos

    def get_primer_info(self, pp_id: str) -> list[PrimerInfo]:
        self.cache_manager.reset()
        pcr_plates: list[NGSPPPlate] = self.run_and_measure_time("===FETCHING PCR PLATES===", 
                                               lambda: self.get_pcr_plates(pp_id=pp_id))
        fwd_rev_sample_list: list[PCRPlateMatch] = self.run_and_measure_time(
            "===FETCHING PCR PLATE INFO FOR " + str(len(pcr_plates)) + " PLATES===", 
            lambda:  self.get_pcr_plate_info(plate_ids=[p.plate_id for p in pcr_plates]))

        fwd_primer_info_list: list[FwdRevClonePrimerInfo] = []
        rev_primer_info_list: list[FwdRevClonePrimerInfo] = []
        clone_list: list[SamplePrimerInfo] = []

        for match in fwd_rev_sample_list:
            print("===PROCESSING MATCH===")
            start_m = time.time()
            fwd_primer_info_list += self.run_and_measure_time(
                "\t===FETCHING FWD PRIMER PLATE INFO===", lambda: self.get_clone_primer_plate_info(match.fwd_plate))
            rev_primer_info_list += self.run_and_measure_time(
                "\t===FETCHING REV PRIMER PLATE INFO===", lambda: self.get_clone_primer_plate_info(match.rev_plate))
            clone_list += self.run_and_measure_time(
                "\t===FETCHING SAMPLE PLATE INFO===", lambda: self.get_sample_plate_info(match.sample_plate))

            stop_m = time.time()   
            elapsed_m = stop_m - start_m
            print("===DONE [" + str(elapsed_m) + "sec]===")

        result: list[PrimerInfo] = []

        for i in range(len(clone_list)):
            fwd: FwdRevClonePrimerInfo = fwd_primer_info_list[i]
            rev: FwdRevClonePrimerInfo = rev_primer_info_list[i]
            info: ClonePrimerInfo = ClonePrimerInfo(
                wellId=clone_list[i].wellId,
                CL=clone_list[i].CL,
                fwdIsSymmetric=fwd.isSymetric,
                fwdIsUnsymetric=fwd.isUnsymetric,
                fwdRobustness=fwd.robustness,
                fwdDirection=fwd.direction,
                fwdPrimer=fwd.primer,
                fwdPrimerType=fwd.primerType,
                fwdPrimerSequence=fwd.primerSequence,
                fwdBcSequence=fwd.bcSequence,
                revIsSymetric=rev.isSymetric,
                revIsUnsymetric=rev.isUnsymetric,
                revRobustness=rev.robustness,
                revDirection=rev.direction,
                revPrimer=rev.primer,
                revPrimerType=rev.primerType,
                revPrimerSequence=rev.primerSequence,
                revBcSequence=rev.bcSequence,
                pcrPlate=rev.pcrPlate
            )

            result.append(info)

        return result

    def get_mutation_info(self, ngs_run_id: str) -> list[MutationInfo]:
        ## initialize output
        result: list[MutationInfo] = []

        ## fetch assay run(s)
        self.cache_manager.reset()
        assay_runs = self.get_assay_runs_for_ngs_run(ngs_run_id=ngs_run_id, schema_id=self.settings.schema_id_mutation_analysis)
        if not assay_runs:
            return result

        ## get assay run properties
        trim_left = assay_runs[0].fields['trimming_left'].value or '0'
        trim_right = assay_runs[0].fields['trimming_right'].value or '0'
        optimization_clone_pool = assay_runs[0].fields['optimization_clone_pool'].text_value
        clone_pool_entity = assay_runs[0].fields['optimization_clone_pool'].value

        ## fetch clone pool
        clone_pool_info = self.benchling.custom_entities.get_by_id(entity_id = str(clone_pool_entity))
        if not clone_pool_info:
            return result

        ## fetch variant library + reference sequences/mutations
        variant_library_id = clone_pool_info.fields['Variant Library(ies)'].value
        if type(variant_library_id) is list:
            variant_library_id = variant_library_id[0]
        variant_library = self.benchling.custom_entities.get_by_id(entity_id = str(variant_library_id))

        ## retrieve reference sequences/mutations
        ref_sequence_aa = self.get_reference_sequence_aa_for_variant_library(variant_library=variant_library) 
        ref_sequence_dna = self.get_reference_sequence_dna_for_variant_library(variant_library=variant_library)
        ref_mutations = self.get_mutations_for_variant_library(variant_library_id=str(variant_library_id))

        info: MutationInfo = MutationInfo(
                trimLeft=str(trim_left), 
                trimRight=str(trim_right),
                optimizationClonePool=optimization_clone_pool, 
                referenceAA=ref_sequence_aa,
                referenceDNA=ref_sequence_dna,
                referenceMutations=ref_mutations
        )
        result.append(info)
        return result

    def get_pcr_pools_field_name(self) -> str:
        return 'PCR Pool(s)'

    def get_pcr_plates_field_name(self) -> str:
        field_definition = self.cache_manager.get_cached_or_execute(
            method_name='benchling.schemas.get_entity_schema_by_id',
            args={'schema_id': self.settings.schema_id_pcr_pool},
            callable = self.benchling.schemas.get_entity_schema_by_id
        ).field_definitions[0]
        return field_definition.name if isinstance(field_definition, SimpleFieldDefinition) else ""

    def get_pcr_pool_for_run(self, ngs_run_id: str) -> Optional[Field]:
        run_entity = self.cache_manager.get_cached_or_execute(
            method_name=' benchling.custom_entities.list.first',
            args={'name_includes': ngs_run_id},
            callable=self.benchling.custom_entities.list
        ).first()
        if not run_entity:
            return None
        return run_entity.fields[self.get_pcr_pools_field_name()]

    def get_pcr_plates(self, pp_id: str) -> list[NGSPPPlate]:

        pcr_plate = self.cache_manager.get_cached_or_execute(
            method_name=" benchling.custom_entities.list.first",
            args={"name": pp_id, "schema_id": self.settings.schema_id_pcr_pool},
            callable=self.benchling.custom_entities.list,
        ).first()
        
        if not pcr_plate:
            return []
        
        pcr_plate_field = pcr_plate.fields[self.get_pcr_plates_field_name()]

        plates_str = pcr_plate_field.text_value or ''
        plates = [s.strip() for s in plates_str.split(',')]

        plate_ids = to_string_list(pcr_plate_field.value)
        ngs_plates: list[NGSPPPlate] = []
        for i in range(len(plate_ids)):
            plate = NGSPPPlate(pcr_plate=plates[i], plate_id=plate_ids[i])
            ngs_plates.append(plate)

        return ngs_plates

    def get_pcr_plate_info(self, plate_ids: list[str]) -> list[PCRPlateMatch]:
        plates: list[Plate] = []

        custom_entities = self.cache_manager.get_cached_or_execute(
            method_name='benchling.plates.list',
            args={'ids': plate_ids},
            callable = self.benchling.plates.list
        )

        for plate_page in custom_entities:
            plates += plate_page

        matches: list[PCRPlateMatch] = []

        for plate in plates:
            fwd_plate = plate.fields['Primer Plate - Forward'].value
            rev_plate = plate.fields['Primer Plate - Reverse'].value
            sample_plate = plate.fields['Sample Plate'].value
            matches.append(PCRPlateMatch(fwd_plate=to_string(fwd_plate), rev_plate=to_string(rev_plate), sample_plate=to_string(sample_plate)))

        return matches

    def assert_well(self, well: Any) -> bool:
        if type(well) is not Well or not well.contents:
            return False
        entity = well.contents[0].entity
        if type(entity) is not Fields:
            return False
        return True

    def get_clone_primer_plate_info(self, plate_id: str) -> list[FwdRevClonePrimerInfo]:
        plates = self.cache_manager.get_cached_or_execute(
            method_name='benchling.plates.list.first',
            args={'ids':[ plate_id ]},
            callable=self.benchling.plates.list
        )
        plate = plates.first()
        if not plate:
            return []

        info_list: list[FwdRevClonePrimerInfo] = []
        wells = plate.wells

        for well_key in wells.additional_keys:
            well = wells.get(well_key)
            if type(well) is not Well or not well.contents or type(well.contents[0].entity) is not DnaSequence:
                continue
            entity = well.contents[0].entity
            fields = entity.fields
            info = FwdRevClonePrimerInfo(self.fields_to_primer_info(fields=fields), wellId=well.barcode, pcrPlate=plate.id)
            info_list.append(info)

        return info_list

    def fields_to_primer_info(self, fields: Fields) -> FwdRevPrimerInfo:
        isSymetric = fields['Barcode - Is Symetric'].text_value
        isUnsymetric = fields['Barcode - Is Unsymetric'].text_value
        robustness = fields['Barcode - Robustness'].text_value
        return FwdRevPrimerInfo(
                isSymetric=bool(isSymetric) if isSymetric else None,
                isUnsymetric=bool(isUnsymetric) if isUnsymetric else None,
                robustness=float(robustness) if robustness and robustness else None,
                direction=fields['Direction'].text_value or "None",
                primer=fields['Primer'].text_value or "None",
                primerType=fields['Primer - Type'].text_value or "None",
                bcSequence=fields['Sequence - Barcode'].text_value or "None",
                primerSequence=fields['Sequence - Primer'].text_value or "None"
            )

    def get_reference_sequence_aa_for_variant_library(self, variant_library) -> str:
        reference_sequence_aa_key = 'Reference Sequence AA'
        sequence_id = get_field_id_from_custom_entity(custom_entity=variant_library, key=reference_sequence_aa_key)
        if not sequence_id:
            return ''
        aa_sequence = self.cache_manager.get_cached_or_execute(
            method_name='benchling.aa_sequences.get_by_id',
            args={
                'aa_sequence_id': sequence_id
            },
            callable=self.benchling.aa_sequences.get_by_id
        )
        if not aa_sequence:
            return ''
        return aa_sequence.amino_acids

    def get_reference_sequence_dna_for_variant_library(self, variant_library) -> str:
        reference_sequence_dna_key = 'Reference Sequence DNA'
        sequence_id = get_field_id_from_custom_entity(custom_entity=variant_library, key=reference_sequence_dna_key)
        if not sequence_id:
            return ''
        dna_sequence = self.cache_manager.get_cached_or_execute(
            method_name='benchling.dna_sequences.get_by_id',
            args={
                'dna_sequence_id': sequence_id
            },
            callable=self.benchling.dna_sequences.get_by_id
        )
        if not dna_sequence:
            return ''
        return dna_sequence.bases

    def get_mutations_for_variant_library(self, variant_library_id: str) -> list:
        ## fetch assay results
        pages = self.benchling.assay_results.list(
            schema_id=self.settings.schema_id_mutation_assay_results, entity_ids=[variant_library_id]
        )
        ## extract reference mutations
        assay_results = []
        for page in pages:
            for result in page:
                assay_results.append(result.fields['mutations'].value)
        return assay_results

    def get_sample_plate_info(self, plate_id: str) -> list[SamplePrimerInfo]:
        plate = self.cache_manager.get_cached_or_execute(
            method_name=' benchling.plates.list.first',
            args={'ids': [plate_id]},
            callable = self.benchling.plates.list).first()
        if not plate:
            return []

        info_list: list[SamplePrimerInfo] = []
        wells = plate.wells

        for well_key in wells.additional_keys:
            well = wells.get(well_key)
            if type(well) is not Well or not well.barcode:
                raise ValueError(f"Failed to read well/well barcode for plate: {plate_id}. Contact the developers if you see this message.") 

            info: SamplePrimerInfo = SamplePrimerInfo(
                wellId=well.barcode,
                CL=well.contents[0].entity.name if len(well.contents) > 0 and isinstance(well.contents[0].entity, CustomEntity) else "EMPTY_CLONE"
            )
            info_list.append(info)
        return info_list

    def create_blob(self, analysis: list, name: str) -> Blob:
        blob_service: BlobService = self.benchling.v2.stable.blobs
        with tempfile.TemporaryFile() as fp:
            to_dump = [a.model_dump(by_alias=True) for a in analysis]
            df = pd.read_json(json.dumps(to_dump, default=pydantic_encoder))
            df.to_csv(path_or_buf=fp)
            fp.seek(0)
            return blob_service.create_from_bytes(input_bytes=fp.read(), name=name)

    def create_blob_purity_analysis(self, purity_analysis: list[PurityAnalysis]) -> Blob:
        return self.create_blob(purity_analysis, name='NGS_Pipeline_Purity_Analysis_Output2.csv')

    def create_blob_repertoire_analysis(self, repertoire_analysis: list[RepertoireAnalysis]) -> Blob:
        return self.create_blob(repertoire_analysis, name='NGS_Pipeline_Repertoire_Analysis_Output2.csv')

    def create_blob_mutation_analysis(self, mutation_analysis: list[MutationPurityAnalysis]) -> Blob:
        return self.create_blob(mutation_analysis[0].mutationAnalysis, name='NGS_Pipeline_Mutation_Analysis_Output2.csv')

    def create_blob_purity_analysis2(self, mutation_analysis: list[MutationPurityAnalysis]) -> Blob:
        return self.create_blob(mutation_analysis[0].purityAnalysis, name='NGS_Pipeline_Purity_Analysis_Output2.csv')

    T = TypeVar('T', bound=Analysis)
    def save_analysis(self, analysis: list[T], create_blob_func: Callable[..., Blob], config_file_name: str, schema_id: str) -> list[T]:
        for analysis_entity in analysis:
            print("=====DEBUG=====")
            print("Fetching Assay Run for given NGS RUN...")
            assay_run_id = self.choose_assay_run_for_ngs_run(ngs_run_id=analysis_entity.ngsRun, schema_id=schema_id)
            if assay_run_id is None:
                raise no_assay_run_found_for_ngs_run_error

            blob = create_blob_func(analysis)
            print(str(f'Starting file upload {config_file_name} ({assay_run_id})'))
            processor_create_req = AutomationOutputProcessorCreate(
                assay_run_id=assay_run_id, # type: ignore
                automation_file_config_name=config_file_name, # type: ignore
                file_id=blob.id, # type: ignore
                complete_with_errors=True # type: ignore
            )
            lab_automation_service: LabAutomationService = self.benchling.v2.stable.lab_automation
            processor: AutomationOutputProcessor = lab_automation_service.create_output_processor(processor_create_req)
            lab_automation_service.process_output(processor.id)
            print(str(f'Completed file upload {config_file_name} ({assay_run_id})'))

        return analysis        

    def save_purity_analysis(self, purity_analysis: list[PurityAnalysis]) -> list[PurityAnalysis]:
        self.cache_manager.reset()
        return self.save_analysis(purity_analysis, self.create_blob_purity_analysis, 
                                  config_file_name="NGS Pipeline Purity Analysis Output", schema_id=self.settings.schema_id_individual_clones)

    def get_assay_runs_for_ngs_run(self, ngs_run_id: str, schema_id: str) -> list[AssayRun]:
        assay_runs: list[AssayRun] = []
        for runs in self.cache_manager.get_cached_or_execute(
            method_name='benchling.assay_runs.list',
            args={'schema_id': schema_id},
            callable = self.benchling.assay_runs.list
        ):
            print("Checking runs")
            for run in runs:
                print("Checking run")
                print(str(run))
                found_ngs_run_id = run.fields["ngs_run" if schema_id == self.settings.schema_id_clone_pool else "ngs_sequencing_run"].text_value or ""
                if found_ngs_run_id == ngs_run_id:
                    assay_runs.append(run)

        if not assay_runs:
            return []

        assay_runs.sort(key=lambda x: x.created_at, reverse=True)

        return assay_runs

    def choose_amplicon_value_for_ngs_run(self, ngs_run_id: str) -> Optional[bool]:
        assay_runs = self.get_assay_runs_for_ngs_run(ngs_run_id=ngs_run_id, schema_id=self.settings.schema_id_clone_pool)
        if assay_runs:

            amplicon = assay_runs[0].fields['amplicon']
            if amplicon and amplicon.text_value:
                return True if amplicon.text_value == 'Yes' else False
        return None

    def choose_assay_run_for_ngs_run(self, ngs_run_id: str, schema_id: str) -> Optional[str]:
        assay_runs = self.get_assay_runs_for_ngs_run(ngs_run_id=ngs_run_id, schema_id=schema_id)

        if assay_runs:
            return assay_runs[0].id
        return None

    def save_repertoire_analysis(self, repertoire_analysis: list[RepertoireAnalysis]) -> list[RepertoireAnalysis]:
        self.cache_manager.reset()
        return self.save_analysis(repertoire_analysis, self.create_blob_repertoire_analysis, 
                                  config_file_name="NGS Pipeline Repertoire Output", schema_id=self.settings.schema_id_clone_pool)

    def save_purity_mutation_analysis(self, mutation_analysis: list[MutationPurityAnalysis]) -> list[MutationPurityAnalysis]:
        ## only need to resolve assay run id once (same for both uploads)
        ## upload 1/2
        self.cache_manager.reset()
        analysis = self.save_analysis(analysis=mutation_analysis, 
                                create_blob_func=self.create_blob_purity_analysis2, 
                                config_file_name="NGS Pipeline Purity Analysis Output",
                                schema_id=self.settings.schema_id_mutation_analysis)  
        ## upload 2/2
        self.cache_manager.reset()  ## 404 error when not resetting cache
        analysis = self.save_analysis(analysis=analysis, 
                                create_blob_func=self.create_blob_mutation_analysis, 
                                config_file_name="NGS Pipeline Mutation Analysis Output",
                                schema_id=self.settings.schema_id_mutation_analysis)
        return analysis

    def get_sample_type(self, pp_id: str) -> str:
        ngs_plates = self.get_pcr_plates(pp_id=pp_id)
        if len(ngs_plates) > 0:
            is_plate = bool(re.search(pattern="^plt", string=ngs_plates[0].plate_id))
            if is_plate:
                return "Clone"
            else:
                return "Clone_Pool"
        else:
            return ""
        
    def get_ngs_run_info(self, pp_id: str, ngs_run_id: str) -> Dict[str, Any]:
        ## fetch data
        self.cache_manager.reset()
        sample_info = self.cache_manager.get_cached_or_execute(
            method_name="benchling.custom_entities.list.first",
            args={"name": pp_id, "schema_id": self.settings.schema_id_pcr_pool},
            callable=self.benchling.custom_entities.list,
        ).first()
        sample_type = self.get_sample_type(pp_id)
        if sample_type == "Clone_Pool":
            ngs_run = self.get_assay_runs_for_ngs_run(ngs_run_id, schema_id = self.settings.schema_id_clone_pool)
            ngs_run_field = "ngs_run"
        else:
            ngs_run = self.get_assay_runs_for_ngs_run(ngs_run_id, schema_id = self.settings.schema_id_mutation_analysis)
            ngs_run_field = "ngs_sequencing_run"
        if len(ngs_run) > 0:
            project = self.benchling.projects.get_by_id(
                project_id = ngs_run[0].project_id
            )
            entry = self.benchling.entries.get_entry_by_id(
                entry_id = ngs_run[0].entry_id
            )
            ## post-process   
            run_info = BenchlingEntity(
                name = ngs_run[0].fields[ngs_run_field].display_value, 
                benchling_api_id = ngs_run[0].fields[ngs_run_field].value,
                benchling_registry_id = ngs_run[0].fields[ngs_run_field].text_value,
                benchling_schema_id = ngs_run[0].schema.id
            )
            pp_info = BenchlingEntity(
                name = sample_info.name,
                benchling_api_id = sample_info.id,
                benchling_registry_id = sample_info.entity_registry_id,
                benchling_schema_id = self.settings.schema_id_pcr_pool 
            )
            type_info = BenchlingEntity(
                name = ngs_run[0].schema.name,
                benchling_schema_id = ngs_run[0].schema.id
            )
            project_info = BenchlingEntity(
                name = project.name,
                benchling_api_id = project.id
            )
            user_info = User(
                id = entry.authors[0].name,
                name = entry.authors[0].id
            )
            entry_info = BenchlingEntity(
                name = entry.name,
                benchling_api_id = entry.id,
                benchling_registry_id = entry.display_id
            )
            json_data = NGSRunInfo(
                ngs_run = run_info,
                ngs_pp = pp_info,
                ngs_type = type_info,
                project = project_info,
                entry = entry_info,
                user = user_info
            )
            return json_data.model_dump()
        else:
            ## should not be reached
            return {}
            
    
