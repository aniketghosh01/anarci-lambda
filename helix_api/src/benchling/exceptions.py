class NoAssayRunFoundForNGSRun(Exception):
    pass

class InvalidPrimerPlateFields(Exception):
    pass

class InvalidNumberOfVariantLibraries(Exception):
    pass

no_assay_run_found_for_ngs_run_error = NoAssayRunFoundForNGSRun()
invalid_primer_plate_fields = InvalidPrimerPlateFields()
invalid_number_of_variant_libraries = InvalidNumberOfVariantLibraries()