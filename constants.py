
STORAGE_TEMP_VALUES_MAP = {"temperature-18to-35": "TEMPERATURE_MINUS_18_TO_MINUS_35",
                           "temperature-60to-85": "TEMPERATURE_MINUS_60_TO_MINUS_85",
                           "temperatureOther": "TEMPERATURE_OTHER", "temperatureRoom": "TEMPERATURE_ROOM",
                           "temperature2to10": "TEMPERATURE_2_TO_10", "temperatureLN": "TEMPERATURE_LN"}

BBMRI_TO_STANDARDIZED_MIABIS_MATERIAL = {
    "NAV": "Other",  # Not available
    "PATHOGEN": "IsolatedMicrobe",
    "RNA": "RNA",
    "FECES": "Faeces",
    "THROAT_SWAB": "Swab",
    "CELL_LINES": "ImmortalizedCellLine",  # or "CancerCellLine" if cancer-specific
    "SERUM": "Serum",
    "CDNA": "DNA",  # Not in standard list — fallback to "Other"
    "TISSUE_FROZEN": "TissueFrozen",
    "SALIVA": "Saliva",
    "BUFFY_COAT": "BuffyCoat",
    "NASAL_SWAB": "Swab",
    "OTHER": "Other",
    "TISSUE_STAINED": "Other",  # Closest match not in list
    "PLASMA": "Plasma",
    "PERIPHERAL_BLOOD_CELLS": "PrimaryCells",
    "MICRO_RNA": "RNA",  # Closest match not directly listed
    "DNA": "DNA",
    "TISSUE_PARAFFIN_EMBEDDED": "TissueFFPE",
    "URINE": "Urine"
}



query_collection = '''
{
    Collections {
        id
        name
      biobank {
        id
      }

        acronym
        description
        url
        contact {
            email
            first_name
            last_name
        }
      country {
        name
      }
      sex {
        name
      }
      age_low
      age_high
      materials {
        name
      }
      storage_temperatures {
        name
      }
      diagnosis_available {
        code
      }
      number_of_donors
      url
      description
      type {
        name
      }
      access_description
    }
}'''

query_biobanks = '''
{
    Biobanks {
        id
        name
        acronym
        country {
            name
        }
        description
        url
        juridical_person
        withdrawn
        contact {
            email
            first_name
            last_name
        }
        quality {
            quality_standard {
                name
            }
        }
    }
}
'''

networks_query = '''
{
    Networks {
        id
        name
        acronym
        description
        url
        juridical_person
        contact {
            email
            first_name
            last_name
        }
    }
}
'''
