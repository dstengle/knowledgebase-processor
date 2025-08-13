from datetime import date, datetime
from typing import Any, Union, List, Optional

from pydantic import BaseModel
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD, SDO as SCHEMA

from knowledgebase_processor.models.kb_entities import KbBaseEntity
from knowledgebase_processor.config.vocabulary import KB


class RdfConverter:
    """
    Converts Knowledge Base entities to RDF graphs.
    """

    def kb_entity_to_graph(self, entity: KbBaseEntity, base_uri_str: str = "http://example.org/kb/") -> Graph:
        """
        Converts a KB entity instance to an rdflib.Graph by dynamically processing
        RDF metadata defined in the Pydantic model's fields and class configuration.

        Args:
            entity: The KbBaseEntity instance to convert.
            base_uri_str: The base URI string to use for constructing entity URIs
                          if kb_id is not already a full URI.

        Returns:
            An rdflib.Graph representing the entity.
        """
        g = Graph()
        g.bind("kb", KB)
        g.bind("schema", SCHEMA)
        g.bind("rdf", RDF)
        g.bind("rdfs", RDFS)
        g.bind("xsd", XSD)

        if "://" in entity.kb_id:
            entity_uri = URIRef(entity.kb_id)
        else:
            entity_uri = URIRef(base_uri_str.rstrip('/') + "/" + entity.kb_id.lstrip('/'))

        added_rdf_types = set()
        rdfs_label_fallback_field_names: List[str] = []
        
        # 1. Process class-level configurations by iterating through MRO
        # rdf_types are cumulative.
        # rdfs_label_fallback_fields are taken from the most specific class defining them.
        
        # First, find the most specific rdfs_label_fallback_fields
        for cls in type(entity).mro():
            if not issubclass(cls, BaseModel):
                continue

            class_config_data: Optional[dict] = None
            if hasattr(cls, 'model_config') and isinstance(getattr(cls, 'model_config', None), dict): # Pydantic v2
                class_config_data = cls.model_config.get('json_schema_extra')
            elif hasattr(cls, 'Config') and hasattr(cls.Config, 'json_schema_extra'): # Pydantic v1
                class_config_data = getattr(cls.Config, 'json_schema_extra', None)

            if isinstance(class_config_data, dict):
                if 'rdfs_label_fallback_fields' in class_config_data:
                    potential_fallback_fields = class_config_data.get('rdfs_label_fallback_fields')
                    if isinstance(potential_fallback_fields, list):
                        rdfs_label_fallback_field_names = potential_fallback_fields
                        break # Found the most specific, stop.
        
        # Then, accumulate all rdf_types from MRO
        for cls in type(entity).mro():
            if not issubclass(cls, BaseModel):
                continue

            class_config_data: Optional[dict] = None
            if hasattr(cls, 'model_config') and isinstance(getattr(cls, 'model_config', None), dict): # Pydantic v2
                class_config_data = cls.model_config.get('json_schema_extra')
            elif hasattr(cls, 'Config') and hasattr(cls.Config, 'json_schema_extra'): # Pydantic v1
                class_config_data = getattr(cls.Config, 'json_schema_extra', None)

            if isinstance(class_config_data, dict):
                rdf_types_for_class = class_config_data.get('rdf_types', [])
                if isinstance(rdf_types_for_class, list):
                    for type_uri_val in rdf_types_for_class:
                        type_uri = URIRef(type_uri_val) if isinstance(type_uri_val, str) else type_uri_val
                        if isinstance(type_uri, URIRef) and type_uri not in added_rdf_types:
                            g.add((entity_uri, RDF.type, type_uri))
                            added_rdf_types.add(type_uri)

        label_added_for_entity = False # True if an explicit label is added from fields

        # 2. Determine how to access model fields based on Pydantic version
        model_fields_accessor: dict = {}
        is_pydantic_v2 = False
        if hasattr(type(entity), 'model_fields'):  # Pydantic v2
            model_fields_accessor = type(entity).model_fields
            is_pydantic_v2 = True
        elif hasattr(entity, '__fields__'):  # Pydantic v1
            model_fields_accessor = entity.__fields__

        # 3. Process field-level properties
        for field_name, field_obj in model_fields_accessor.items():
            value = getattr(entity, field_name, None)

            if value is None:
                continue

            rdf_meta: Optional[dict] = None
            if is_pydantic_v2: # Pydantic v2: field_obj is FieldInfo
                rdf_meta = getattr(field_obj, 'json_schema_extra', None)
                if rdf_meta is None and hasattr(field_obj, 'extra'): 
                    rdf_meta = field_obj.extra
            else: # Pydantic v1: field_obj is ModelField
                if hasattr(field_obj, 'field_info') and hasattr(field_obj.field_info, 'extra'):
                    rdf_meta = field_obj.field_info.extra
            
            if not isinstance(rdf_meta, dict): 
                rdf_meta = {}

            properties_to_process_uris: List[URIRef] = []
            raw_props = rdf_meta.get('rdf_properties', [])
            if isinstance(raw_props, list):
                for p in raw_props:
                    properties_to_process_uris.append(URIRef(p) if isinstance(p, str) else p)
            
            raw_prop = rdf_meta.get('rdf_property')
            if raw_prop:
                properties_to_process_uris.append(URIRef(raw_prop) if isinstance(raw_prop, str) else raw_prop)

            is_object_prop = rdf_meta.get('is_object_property', False)
            rdf_datatype_uri_str = rdf_meta.get('rdf_datatype')
            rdf_datatype_uri = URIRef(rdf_datatype_uri_str) if rdf_datatype_uri_str else None
            
            current_field_values: List[Any] = []
            if isinstance(value, list):
                current_field_values.extend(value)
            else:
                current_field_values.append(value)

            for p_uri in properties_to_process_uris:
                if not isinstance(p_uri, URIRef): continue

                for item_val in current_field_values:
                    if item_val is None:
                        continue

                    rdf_object: Union[URIRef, Literal]
                    if is_object_prop:
                        item_val_str = str(getattr(item_val, 'kb_id', item_val))
                        
                        if "://" in item_val_str:
                            rdf_object = URIRef(item_val_str)
                        else:
                            rdf_object = URIRef(base_uri_str.rstrip('/') + "/" + item_val_str.lstrip('/'))
                    else:
                        effective_datatype = rdf_datatype_uri
                        if isinstance(item_val, str) and effective_datatype is None:
                            effective_datatype = XSD.string
                        rdf_object = Literal(item_val, datatype=effective_datatype)
                    
                    g.add((entity_uri, p_uri, rdf_object))
                    if p_uri == RDFS.label and item_val is not None: 
                        if isinstance(item_val, str) and item_val.strip() == "":
                            pass 
                        else:
                            label_added_for_entity = True
        
        # 4. Apply class-defined rdfs:label fallback if no explicit label was added
        if not label_added_for_entity and rdfs_label_fallback_field_names:
            for fallback_field_name in rdfs_label_fallback_field_names:
                # Defensive check: ensure fallback_field_name is a string and an attribute
                if not isinstance(fallback_field_name, str) or not hasattr(entity, fallback_field_name):
                    continue
                
                fallback_value = getattr(entity, fallback_field_name, None)
                if fallback_value is not None:
                    fallback_value_str = str(fallback_value)
                    if fallback_value_str.strip(): 
                        g.add((entity_uri, RDFS.label, Literal(fallback_value_str, datatype=XSD.string)))
                        break # Stop after the first successful fallback

        return g