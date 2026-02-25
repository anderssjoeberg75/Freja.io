# 🌅 Morgon-Briefing 2026-02-24 17:38

Error generating briefing: 47 validation errors for _GenerateContentParameters
contents.Content
  Input should be a valid dictionary or object to extract fields from [type=model_attributes_type, input_value=[{'role': 'user', 'parts'...sh token configured.']}], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/model_attributes_type
contents.str
  Input should be a valid string [type=string_type, input_value=[{'role': 'user', 'parts'...sh token configured.']}], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/string_type
contents.is-instance[Image]
  Input should be an instance of Image [type=is_instance_of, input_value=[{'role': 'user', 'parts'...sh token configured.']}], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/is_instance_of
contents.File
  Input should be a valid dictionary or object to extract fields from [type=model_attributes_type, input_value=[{'role': 'user', 'parts'...sh token configured.']}], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/model_attributes_type
contents.Part
  Input should be a valid dictionary or object to extract fields from [type=model_attributes_type, input_value=[{'role': 'user', 'parts'...sh token configured.']}], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/model_attributes_type
contents.list[union[str,is-instance[Image],File,Part]].0.str
  Input should be a valid string [type=string_type, input_value={'role': 'user', 'parts':...lues in memory yet.\n']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/string_type
contents.list[union[str,is-instance[Image],File,Part]].0.is-instance[Image]
  Input should be an instance of Image [type=is_instance_of, input_value={'role': 'user', 'parts':...lues in memory yet.\n']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/is_instance_of
contents.list[union[str,is-instance[Image],File,Part]].0.File.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='user', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].0.File.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['Du är Freja (Digital A...alues in memory yet.\n'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].0.Part.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='user', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].0.Part.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['Du är Freja (Digital A...alues in memory yet.\n'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].1.str
  Input should be a valid string [type=string_type, input_value={'role': 'model', 'parts': ['System ready.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/string_type
contents.list[union[str,is-instance[Image],File,Part]].1.is-instance[Image]
  Input should be an instance of Image [type=is_instance_of, input_value={'role': 'model', 'parts': ['System ready.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/is_instance_of
contents.list[union[str,is-instance[Image],File,Part]].1.File.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='model', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].1.File.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['System ready.'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].1.Part.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='model', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].1.Part.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['System ready.'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].2.str
  Input should be a valid string [type=string_type, input_value={'role': 'user', 'parts':...esh token configured.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/string_type
contents.list[union[str,is-instance[Image],File,Part]].2.is-instance[Image]
  Input should be an instance of Image [type=is_instance_of, input_value={'role': 'user', 'parts':...esh token configured.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/is_instance_of
contents.list[union[str,is-instance[Image],File,Part]].2.File.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='user', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].2.File.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['Du är Freja, en hjälp...resh token configured.'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].2.Part.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='user', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[str,is-instance[Image],File,Part]].2.Part.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['Du är Freja, en hjälp...resh token configured.'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].0.Content.parts.0
  Input should be a valid dictionary or object to extract fields from [type=model_attributes_type, input_value='Du är Freja (Digital Ad...values in memory yet.\n', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/model_attributes_type
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].0.str
  Input should be a valid string [type=string_type, input_value={'role': 'user', 'parts':...lues in memory yet.\n']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/string_type
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].0.is-instance[Image]
  Input should be an instance of Image [type=is_instance_of, input_value={'role': 'user', 'parts':...lues in memory yet.\n']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/is_instance_of
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].0.File.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='user', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].0.File.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['Du är Freja (Digital A...alues in memory yet.\n'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].0.Part.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='user', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].0.Part.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['Du är Freja (Digital A...alues in memory yet.\n'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].0.list[union[str,is-instance[Image],File,Part]]
  Input should be a valid list [type=list_type, input_value={'role': 'user', 'parts':...lues in memory yet.\n']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/list_type
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].1.Content.parts.0
  Input should be a valid dictionary or object to extract fields from [type=model_attributes_type, input_value='System ready.', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/model_attributes_type
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].1.str
  Input should be a valid string [type=string_type, input_value={'role': 'model', 'parts': ['System ready.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/string_type
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].1.is-instance[Image]
  Input should be an instance of Image [type=is_instance_of, input_value={'role': 'model', 'parts': ['System ready.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/is_instance_of
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].1.File.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='model', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].1.File.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['System ready.'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].1.Part.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='model', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].1.Part.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['System ready.'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].1.list[union[str,is-instance[Image],File,Part]]
  Input should be a valid list [type=list_type, input_value={'role': 'model', 'parts': ['System ready.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/list_type
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].2.Content.parts.0
  Input should be a valid dictionary or object to extract fields from [type=model_attributes_type, input_value='Du är Freja, en hjälps...fresh token configured.', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/model_attributes_type
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].2.str
  Input should be a valid string [type=string_type, input_value={'role': 'user', 'parts':...esh token configured.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/string_type
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].2.is-instance[Image]
  Input should be an instance of Image [type=is_instance_of, input_value={'role': 'user', 'parts':...esh token configured.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/is_instance_of
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].2.File.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='user', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].2.File.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['Du är Freja, en hjälp...resh token configured.'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].2.Part.role
  Extra inputs are not permitted [type=extra_forbidden, input_value='user', input_type=str]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].2.Part.parts
  Extra inputs are not permitted [type=extra_forbidden, input_value=['Du är Freja, en hjälp...resh token configured.'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.12/v/extra_forbidden
contents.list[union[Content,str,is-instance[Image],File,Part,list[union[str,is-instance[Image],File,Part]]]].2.list[union[str,is-instance[Image],File,Part]]
  Input should be a valid list [type=list_type, input_value={'role': 'user', 'parts':...esh token configured.']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.12/v/list_type