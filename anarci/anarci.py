# Workflow based on https://github.com/oxpig/ANARCI/issues/39
# Number using ANARCI, followed by annotation.
# IGMT rules: https://www.imgt.org/IMGTScientificChart/Nomenclature/IMGT-FRCDRdefinition.html
# Kabat rules: http://www.bioinf.org.uk/abs/info.html

from pickle import FALSE
import subprocess
import tempfile
import re
from typing import Text
import pandas as pd

ANARCI_IMAGE='anarci'
ANARCI_SPECIES_OPTIONS = ['human', 'mouse', 'rat', 'rabbit', 'rhesus', 'pig', 'alpaca', 'cow']
ANARCI_CHAIN_TYPE_OPTIONS=['ig','tr','heavy','light','H','K','L','A','B']
ANARCI_DOCKERFILE = 'https://github.com/bayer-int/biologics-research-helix-wrapper-api/blob/main/anarci/Dockerfile'

def get_anarci_species(species:str) -> str:
    """
    Use ANARCI compatible species

    E.g. 'Homo Sapiens' would get translated into input argument 'human'.

    Args
        species: a species name
    Returns
        species that can be given as input to ANARCI
    """
    if species is None:
        return None
    
    anarci_species = species
    if (species.lower() in ['homo sapiens', 'humanized']):
        anarci_species = 'human'
    if (species.lower() in ['mus musculus']):
        anarci_species = 'mouse'
    if (species.lower() in ['rattus norvegicus']):
        anarci_species = 'rat'
    if (species.lower() in ['camelus dromedarius']):
        anarci_species = None
    if (species.lower() in ['lama glama']):
        anarci_species = None
    if (species.lower() in ['n/a', 'human-mouse chimera']):
        anarci_species = None
    if (species.lower() in ['vicugna pacos']):
        anarci_species = 'alpaca'

    if  anarci_species not in ANARCI_SPECIES_OPTIONS:
        print(f'No ANARCI input species found for {species}')

    return anarci_species


def get_anarci_chain_type(chain_type:str) -> str:
    """
    Use ANARCI compatible chain type

    E.g. 'VL-kappa' would get translated into input argument 'K'.

    Args
        chain_type: a chain type following bayer internal conventions
    Returns
        chain_type(str) that can be given as input to ANARCI
    """
    # TODO: hint to seq type
    # Light: LC, LC-kappa, LC-lambda, VL, VL-kappa, VL-lambda
    # Heavy: VH HC
    if chain_type is None:
        return None
    
    if chain_type in ANARCI_CHAIN_TYPE_OPTIONS:
        return chain_type

    anarci_chain_type = chain_type

    if (anarci_chain_type =='LC'):
        anarci_chain_type = 'light'
    if (anarci_chain_type =='LC-kappa'):
        anarci_chain_type = 'light'
    if (anarci_chain_type =='LC-lambda'):
        anarci_chain_type = 'light'
    if (anarci_chain_type =='VL'):
        anarci_chain_type = 'light'
    if (anarci_chain_type =='VL-kappa'):
        anarci_chain_type = 'light'
    if (anarci_chain_type =='VL-lambda'):
        anarci_chain_type = 'light'
    if (anarci_chain_type =='VH'):
        anarci_chain_type = 'heavy'
    if (anarci_chain_type =='HC'):
        anarci_chain_type = 'heavy'

    if  anarci_chain_type not in ANARCI_CHAIN_TYPE_OPTIONS:
        print(f'No ANARCI input species found for {chain_type}')

    return anarci_chain_type


def annotate_seq(seq: str, species:str = None,  chain_type:str = None) -> dict:
    """
    Args:
        seq: str
        species: {human,mouse,rat,rabbit,rhesus,pig,alpaca,cow}
        chain_type: ['ig','tr','heavy','light','H','K','L','A','B']
    Returns: dict
        {
        metadata_kabat: dict
        metadata_imgt: dict
        annotation: {annotation*: subseq}
        }
        Where subseq are parts of the original sequence.
        
    Example:
        annotate_seq(
          seq = 'QVQLVESGGGLVQPGGSLRLACAGSGSISSIFRMGWYRQAPGKQRELVATIIRGGYTNYGDSVKGRFTISRDNAENTAYLQMNTLKPEDTAVYYCNAYIRSGTTRDYWGQGTQVTVSS'
          species = 'human'
        )
    """
    assert (species is None) or (species in ANARCI_SPECIES_OPTIONS)
    annotation_imgt = annotate_seq_imgt(seq = seq, species=species, chain_type=chain_type)
    annotation_kabat = annotate_seq_kabat(seq = seq, species=species, chain_type=chain_type)

    annotation = annotation_imgt['annotation'] | annotation_kabat['annotation']
    return {
        'metadata_kabat': annotation_kabat['metadata'],
        'metadata_imgt': annotation_imgt['metadata'],
        'annotation': annotation
    }

def annotate_seq_imgt(seq: str, species:str = None, chain_type:str=None) -> dict:
    anarci_output = anarci_number(seq = seq,species= species, chain_type=chain_type, scheme='imgt')
    df = anarci_output['numbering']
    metadata = anarci_output['metadata']
    chain = metadata['chain_type']
    df['annotation'] = [annotate_IMGT(i,chain=chain) for i in df['number']]
    df=df[~(df['AA'] == '-')]
    df=df[['annotation', 'AA']].groupby('annotation', as_index=False).agg(''.join)
    annotation = dict(zip(df.annotation, df.AA))
    return {
        'metadata': metadata,
        'annotation': annotation
    }

def annotate_seq_kabat(seq: str, species:str = None, chain_type:str=None)-> dict:
    anarci_output = anarci_number(seq = seq,species= species, chain_type=chain_type, scheme='kabat')
    df = anarci_output['numbering']
    metadata = anarci_output['metadata']
    chain = metadata['chain_type']
    df['annotation'] = [annotate_Kabat(i, chain=chain) for i in df['number']]
    df=df[~(df['AA'] == '-')]
    df=df[['annotation', 'AA']].groupby('annotation', as_index=False).agg(''.join)
    annotation = dict(zip(df.annotation, df.AA))
    return {
        'metadata': metadata,
        'annotation': annotation
    }

def anarci_number(seq: str, species:str=None, chain_type:str=None, scheme:str = 'imgt') -> dict:
    """
    Ensure to have anarci installed using docker first.
    Args:
        seq: str
        species: str {human,mouse,rat,rabbit,rhesus,pig,alpaca,cow}
        scheme: str {imgt, kabat}

    Returns: dict
    {
    numbering: DataFrame
        - type (str)
        - number (int)
        - AA (str)
    metadata: 
        {
        'species': str,
        'chain_type': str,
        'e-value': '2.2e-54',
        'score': '174.1',
        'seqstart_index': int,
        'seqend_index': int,
        'ANARCI_VERSION': str
        'ANARCI_DOCKERFILE': str
        }
    }

    """
    allowed_schemes = ['imgt', 'kabat']
    assert scheme in allowed_schemes
    assert (species is None) or (species in ANARCI_SPECIES_OPTIONS)
    assert (chain_type is None) or (chain_type in ANARCI_CHAIN_TYPE_OPTIONS)

    if species is None:
        species_flag = ''
    else:
        species_flag = f"--use_species='{species}'"

    if chain_type is None:
        chain_type_flag = ''
    else:
        chain_type_flag = f"--restrict='{chain_type}'"

    # Using temporary file for the sequence prevents command injection.
    # Therefore preferred over command line argument.
    with tempfile.NamedTemporaryFile(mode = "r") as outputfile:
        with tempfile.NamedTemporaryFile() as inputfile:
            with open(inputfile.name, 'w') as infile:
                infile.write(">test \n")
                infile.write(seq)
            print('running anarci')
            cmd = f"""
            docker run \
            --volume={inputfile.name}:/in.fasta:ro \
            --volume={outputfile.name}:/anarci_output.txt \
            {ANARCI_IMAGE} ANARCI \
            -i /in.fasta \
            -o /anarci_output.txt \
            {species_flag} \
            {chain_type_flag} \
            --scheme='{scheme}' 
            """
            subprocess.call(cmd, shell=True)
            output = outputfile.read()

    df = __anarci_to_df(output)
    metadata = __anarci_to_metadata(output)

    ANARCI_VERSION =  subprocess.run(
        f'docker run {ANARCI_IMAGE} head ANARCI_VERSION',
        shell=True,
        capture_output=True, text=True).stdout.strip('\n')
    
    metadata['ANARCI_VERSION'] = ANARCI_VERSION
    metadata['ANARCI_DOCKERFILE'] = ANARCI_DOCKERFILE
    
    result = {
        'numbering':df,
        'metadata': metadata
    }

    return(result)


def __anarci_to_df(anarci_output:str) -> pd.DataFrame:
    """
    Convert anarci output to dataframe
    input: str: anarci output
    output: dataframe
    """
    # remove comments
    numbering = re.sub('#.*\n', '',anarci_output)
    # remove end of file
    numbering = re.sub('//.*', '',numbering)
    # split lines and remove last line containing only newline
    numbering = numbering.splitlines()
    numbering = numbering[0:-1]
    
    # process to dataframe
    rows = []
    for x in numbering:
        split = x.split()

        # Sometimes ABC suffix for repeating numbers
        # e.g.
        # 81 L
        # 82 A K
        # 82 B S
        # 82 C L
        # --> Here we the KSL and not ABC
        if (len(split) == 4):
            AA = split[3]
        else:
            AA = split[2]
        row = pd.DataFrame({
            'type': [split[0]],
            'number': [int(split[1])],
            "AA":  [AA]
        })
        rows.append(row)
    df = pd.concat(rows)

    return(df)


def __anarci_to_metadata(anarci_output: str) -> dict:
    """
    Convert anarci output to dataframe
    args:
        anarci output (str)
    return: dict
        {
        'species': str,
        'chain_type': str,
        'e-value': float,
        'score': float,
        'seqstart_index': int,
        'seqend_index': int
        }

    example:
        anarci_output = '''
        # test
        # ANARCI numbered
        # Domain 1 of 1
        # Most significant HMM hit
        #|species|chain_type|e-value|score|seqstart_index|seqend_index|
        #|mouse|K|2.2e-54|174.1|0|109|
        # Scheme = kabat
        L 1       D
        '''
        __anarci_to_metadata(anarci_output)

    """
    lines = anarci_output.split('\n')
    metadata_headers_i = [i for i, item in enumerate(lines) if re.search('#\\|species\\|chain_type\\|.*', item)][0]
    
    headers = lines[metadata_headers_i].split('|')
    headers.remove('#')
    headers.remove('')

    values = lines[metadata_headers_i + 1].split('|')
    values.remove('#')
    values.remove('')

    expected_headers = ['species', 'chain_type','e-value', 'score', 'seqstart_index', 'seqend_index']
    assert set(expected_headers).issubset(set(headers))
    assert len(headers) == len(values)

    metadata = dict(zip(headers,values))
    metadata = {k: metadata[k] for k in expected_headers}
    metadata['seqstart_index'] = int(metadata['seqstart_index'])
    metadata['seqend_index'] = int(metadata['seqend_index'])
    metadata['score'] = float(metadata['score'])
    metadata['e-value'] = float(metadata['e-value'])

    return(metadata)


def annotate_IMGT(number:int, chain:str) -> str:
    """
    Follows official definition: https://www.imgt.org/IMGTScientificChart/Nomenclature/IMGT-FRCDRdefinition.html
    Args:
        - numbering (int): according to Kabat
        - chain (str): Which chain the residue is on.
          'K' -> Kappa Light
          'L' -> Lamda Light
          'H' -> Heavy
    returns one of following strings:
        - 'FR1_IMGT'
        - 'CDR1_IMGT'
        - 'FR2_IMGT'
        - 'CDR2_IMGT'
        - 'FR3_IMGT'
        - 'CDR3_IMGT'
        - 'FR4_IMGT'
    """
    assert chain in ['H', 'L', 'K']

    if chain in ['K', 'L']:    
        if 1 <= number <= 35:
            a = 'FR1_IMGT'
        elif 36 <= number <= 40:
            a = 'CDR1_IMGT'
        elif 41 <= number <= 54:
            a = 'FR2_IMGT'
        elif 55 <= number <= 74:
            a = 'CDR2_IMGT'
        elif 75 <= number <= 104:
            a = 'FR3_IMGT'
        elif 105 <= number <= 117:
            a = 'CDR3_IMGT'
        elif 118 <= number: # FIXME: figure out end
            a = 'FR4_IMGT'
        else:
            a =  None

    if chain == 'H':
        if 1 <= number <= 26:
            a = 'FR1_IMGT'
        elif 27 <= number <= 38:
            a = 'CDR1_IMGT'
        elif 39 <= number <= 55:
            a = 'FR2_IMGT'
        elif 56 <= number <= 65:
            a = 'CDR2_IMGT'
        elif 66 <= number <= 104:
            a = 'FR3_IMGT'
        elif 105 <= number <= 117:
            a = 'CDR3_IMGT'
        elif 118 <= number <= 129:
            a = 'FR4_IMGT'
        else:
            a =  None

    return a
    

def annotate_Kabat(number:int, chain) -> str:
    """
    Follows official definition as provided here: http://www.bioinf.org.uk/abs/info.html
    Args: number
        - numbering (int): according to Kabat
        - chain (str): Which chain the residue is on.
          'K' -> Kappa Light
          'L' -> Lamda Light
          'H' -> Heavy
    returns one of following strings:
        - 'FR1_Kabat'
        - 'CDR1_Kabat'
        - 'FR2_Kabat'
        - 'CDR2_Kabat'
        - 'FR3_Kabat'
        - 'CDR3_Kabat'
        - 'FR4_Kabat'
    """
    assert chain in ['H', 'L', 'K']

    if chain in ['K', 'L']:    
        if 1 <= number <= 23:
            a = 'FR1_Kabat'
        elif 24 <= number <= 34:
            a = 'CDR1_Kabat'
        elif 35 <= number <= 49:
            a = 'FR2_Kabat'
        elif 50 <= number <= 56:
            a = 'CDR2_Kabat'
        elif 57 <= number <= 88:
            a = 'FR3_Kabat'
        elif 89 <= number <= 97:
            a = 'CDR3_Kabat'
        elif 98 <= number: # FIXME: figure out end
            a = 'FR4_Kabat'
        else:
            a =  None

    if chain == 'H':    
        if 1 <= number <= 30:
            a = 'FR1_Kabat'
        elif 31 <= number <= 35:
            a = 'CDR1_Kabat'
        elif 36 <= number <= 49:
            a = 'FR2_Kabat'
        elif 50 <= number <= 65:
            a = 'CDR2_Kabat'
        elif 66 <= number <= 94:
            a = 'FR3_Kabat'
        elif 95 <= number <= 102:
            a = 'CDR3_Kabat'
        elif 103 <= number:  # FIXME: figure out end
            a = 'FR4_Kabat'
        else:
            a =  None
    
    return a
    