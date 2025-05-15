import json
from typing import List
import simple_icd_10
import requests
from miabis_model import Biobank, Collection, Network, Gender
from miabis_model.storage_temperature import parse_storage_temp_from_code
from blaze_client import BlazeClient

from constants import BBMRI_TO_STANDARDIZED_MIABIS_MATERIAL, STORAGE_TEMP_VALUES_MAP, query_biobanks, query_collection, \
    networks_query

blaze_client = BlazeClient("http://localhost:8080/fhir", "", "")


def populate_collections(json_data: dict) -> list[Collection]:
    collections = []
    for collection_json in json_data.get("data", {}).get("Collections", []):
        # Extract necessary fields from the JSON
        identifier = collection_json.get("id")
        name = collection_json.get("name")
        description = collection_json.get("description")
        contact_info = collection_json.get("contact", {})  # Extract contact info from nested object
        country = collection_json.get("country").get("name")  # Extract country name from nested object
        sex = collection_json.get("sex", [])  # Extract gender information
        age_low = collection_json.get("age_low")
        age_high = collection_json.get("age_high")
        storage_temperatures = collection_json.get("storage_temperatures", [])  # Extract storage temperatures
        diagnoses = collection_json.get("diagnosis_available", [])
        sample_types = [sample_type.get("name") for sample_type in collection_json.get("materials", {})]
        sample_types_standardized = [BBMRI_TO_STANDARDIZED_MIABIS_MATERIAL.get(sample_type, "Other") for sample_type in
                                     sample_types]
        managing_biobank_id = collection_json.get("biobank", {}).get("id", "")  # Extract managing biobank ID

        # Extract contact details
        contact_name = contact_info.get("first_name", "unknown")
        contact_surname = contact_info.get("last_name", "unknown")
        contact_email = contact_info.get("email", "unknown")

        # Map genders to Gender enum
        genders = [
            Gender[("UNKNOWN" if (name := g.get("name")) in (
                "NAV", "NASK", "UNDIFFERENTIAL", "*", "NEUTERED_MALE", "NEUTERED_FEMALE") else name).upper()]
            for g in sex
            if g.get("name") is not None
        ]

        storage_temperatures = [parse_storage_temp_from_code(STORAGE_TEMP_VALUES_MAP, storage_temp.get("name", "")) for
                                storage_temp in storage_temperatures]

        # Extract diagnosis codes
        diagnosis_codes = [diagnosis.get("code") for diagnosis in diagnoses if
                           simple_icd_10.is_valid_item(diagnosis.get("code", ""))]

        # Create a Collection instance
        try:
            collection = Collection(
                identifier=identifier,
                name=name,
                managing_biobank_id=managing_biobank_id,
                contact_name=contact_name,
                contact_surname=contact_surname,
                contact_email=contact_email,
                country=country,
                genders=genders,
                material_types=sample_types_standardized,
                storage_temperatures=storage_temperatures,
                age_range_low=age_low,
                age_range_high=age_high,
                diagnoses=diagnosis_codes,
                description=description
            )
        except ValueError as e:
            print(f"Error creating Collection: {e}")
            continue

        collections.append(collection)

    return collections


def populate_biobanks(json_data: dict) -> List[Biobank]:
    biobanks = []
    juristic_persons = {}
    for biobank_json in json_data.get("data", {}).get("Biobanks", []):
        # Extract necessary fields from the JSON
        identifier = biobank_json.get("id")
        name = biobank_json.get("name")
        alias = biobank_json.get("acronym", "unknown")
        juristic_person = biobank_json.get("juridical_person")
        country = biobank_json.get("country", {}).get("name", "")  # Extract country name from nested object
        description = biobank_json.get("description")
        contact_info = biobank_json.get("contact", {})  # Extract contact info from nested object

        # Extract contact details
        contact_name = contact_info.get("first_name", "unknown")
        contact_surname = contact_info.get("last_name", "unknown")
        contact_email = contact_info.get("email", "unknown")

        # Extract quality management standards
        quality_management_standards = fetch_quality_names(biobank_json.get("quality", []))

        # Create a Biobank instance
        biobank = Biobank(
            identifier=identifier,
            name=name,
            alias=alias,
            country=country,
            juristic_person=juristic_person,
            contact_name=contact_name,
            contact_surname=contact_surname,
            contact_email=contact_email,
            quality__management_standards=quality_management_standards,
            # Not available in the JSON, leave as empty string
            description=description
        )
        jp_name = biobank.juristic_person.name

        if juristic_persons.get(jp_name) is None:
            juristic_persons[jp_name] = 1
        else:
            juristic_persons[jp_name] += 1

        biobanks.append(biobank)

    return biobanks


def populate_networks(json_data: dict) -> list[Network]:
    """
    This function parses and creates List of Networks
    :param json_data: json to be parsed
    :return: Tuple containing List of Networks
    """
    networks = []
    juristic_persons = {}
    for network_json in json_data.get("data", {}).get("Networks", []):
        # Extract necessary fields from the JSON
        identifier = network_json.get("id")
        name = network_json.get("name")
        description = network_json.get("description", "")
        juristic_person = network_json.get("juridical_person", "unknown")
        contact_info = network_json.get("contact", {})  # Extract contact info from nested object
        country = network_json.get("national_node", "unknown")
        common_collaboration_topics = network_json.get("common_network_elements", "").split(",") if network_json.get(
            "common_network_elements") else []

        # Extract contact details
        contact_name = contact_info.get("first_name", "unknown")
        contact_surname = contact_info.get("last_name", "unknown")
        contact_email = contact_info.get("email", "unknown")

        # Assuming managing_biobank_id is not directly available in the JSON, you might need to derive it
        managing_biobank_id = "bbmri-eric:ID:AT_MUG"  # Replace with actual logic to get this value

        # Create a Network instance
        network = Network(
            identifier=identifier,
            name=name,
            contact_email=contact_email,
            country=country,
            juristic_person=juristic_person,
            members_collections_ids=[],  # Replace with actual member collection IDs if available
            members_biobanks_ids=[],  # Replace with actual member biobank IDs if available
            contact_name=contact_name,
            contact_surname=contact_surname,
            common_collaboration_topics=common_collaboration_topics,
            description=description
        )
        jp_name = network.network_organization.juristic_person.name
        if juristic_persons.get(jp_name) is None:
            juristic_persons[jp_name] = 1
        else:
            juristic_persons[jp_name] += 1
        networks.append(network)

    return networks


def fetch_quality_names(quality_data: list) -> List[str]:
    """
    Fetch all 'name' fields under the 'quality -> quality_standard -> name' path.
    """
    names = []
    for item in quality_data:
        quality_standard = item.get("quality_standard", {})
        name = quality_standard.get("name")
        if name:
            names.append(name)
    return names


def transform_biobanks()-> True:
    response = requests.post("https://directory.bbmri-eric.eu/ERIC/directory/graphql",
                             json={'query': query_biobanks})
    if response.status_code == 200:
        json_data = response.json()
        biobanks_count = len(json_data.get("data").get("Biobanks"))
        print(f'number of biobanks from request:{biobanks_count} ')
        biobanks = populate_biobanks(json_data)
        print(f'number of biobanks after the transformation: {len(biobanks)}')

        for i,biobank in enumerate(biobanks):
            print("uploading biobank number:", i)
            blaze_client.upload_biobank(biobank)
        print("INFO : biobank Upload to blaze ended.")

def transform_collections():
    response = requests.post("https://directory.bbmri-eric.eu/ERIC/directory/graphql",
                             json={'query': query_collection})
    if response.status_code == 200:
        json_data = response.json()
        collections_count = len(json_data.get("data").get("Collections"))
        print(f'number of Collections from request:{collections_count} ')
        collections = populate_collections(json_data)
        print(f'number of collections after the transformation: {len(collections)}')
        for i, collection in enumerate(collections):
            print("uploading collection number:", i)
            blaze_client.upload_collection(collection)


def transform_networks():
    response = requests.post("https://directory.bbmri-eric.eu/ERIC/directory/graphql",
                             json={'query': networks_query})
    if response.status_code == 200:
        json_data = response.json()
        networks_count = len(json_data.get("data").get("Networks"))
        print(f'number of Networks from request:{networks_count} ')
        networks = populate_networks(json_data)
        print(f'number of networks after the transformation: {len(networks)}')
        for i,network in enumerate(networks):
            print("uploading Network number:", i)
            blaze_client.upload_network(network)


transform_biobanks()
transform_networks()
transform_collections()
