from __future__ import annotations
import logging


class ResponseValidator:
    # this class checks if the AI output follows the required schema and additional rules. It is used in AIManager to validate the AI output before further processing.
    def __init__(self):
        self.__logger = logging.getLogger(__name__)
        self.__schema = {
            "ai_category": [str, ("food_quality", "service", "hygiene", "billing", "other")],
            "key_details": [list, None],
            "severity": [str, ("low", "medium", "high")],
            "reason": [str, None],
            "reputational_risk": [bool, None],
            "confidence": [str, ("low", "medium", "high")]
        }

    def _check_schema_fields(self, ai_output: dict) -> bool: # checks if each schema field exists in the ai_output, has the correct data type and allowed value
        # Protected method, only used by validate_ai_response() inside this class. Do not call it directly.
        schema = self.__schema
        for field, rule in schema.items(): # field = key, rule = values. e.g. field = severity, rule = [str, ("low", "medium", "high")]
            if field not in ai_output: # if a schema field is missing in ai_output, log error
                self.__logger.error(f"missing field: {field}")
                return False
            
            data_value = ai_output[field]

            if not isinstance(data_value, rule[0]): # if ai_output data type is not the same as schema, log error
                self.__logger.error(f"wrong data type for {field}")
                return False

            if rule[1] is not None and data_value not in rule[1]: # if allowable value != None and data value is not in the allowable values, log error
                self.__logger.error(f"invalid value: {data_value} for field: {field}")
                return False

        return True


    def _check_additional_rules(self, ai_output: dict) -> bool: # checks whether key details items all are of type string and reason is not empty
        # Protected method, only used by validate_ai_response() inside this class. Do not call it directly.
        for item in ai_output["key_details"]:
            if not isinstance(item, str): # if item data type is not string, log error
                self.__logger.error(f"key_details item is not a string: {item}")
                return False
            
        reason_value = ai_output["reason"]

        if not reason_value.strip(): # checks if reason value is empty, if empty log error
            self.__logger.error("reason value is empty")
            return False

        return True


    def validate_ai_response(self, ai_output: dict | None) -> bool: # validate that the AI output follows the required schema
        # Public method, can be called from outside this class in AIManager to validate the AI output before further processing.
        if not isinstance(ai_output, dict): # rejects None or non-dictionary ai_output from a failed parse
            self.__logger.error("ai_output data type is not a dictionary")
            return False
        
        if not self._check_schema_fields(ai_output): # if _check_schema_fields function is false, return false
            return False
        
        if not self._check_additional_rules(ai_output): # if _check_additional_rules function is false, return false
            return False
        
        return True