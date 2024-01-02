"""
Pydantic provides various constraints and validation features for string, integer, float, and other types. Let's go through the most commonly used constraints:

### 1. Strings (`constr`):

- `min_length`: Minimum length of the string.
- `max_length`: Maximum length of the string.
- `regex`: Validates the string with the provided regular expression.
- `strip_whitespace`: If `True`, leading and trailing whitespaces are stripped.
- `curtail_length`: If a string exceeds the `max_length`, it will truncate it to this length.

Example:

```python
from pydantic import constr

name: constr(min_length=2, max_length=10, regex=r'^[a-zA-Z]+$')
```

### 2. Integers (`conint`):

- `gt`: Greater than a specific value.
- `ge`: Greater than or equal to a specific value.
- `lt`: Less than a specific value.
- `le`: Less than or equal to a specific value.
- `multiple_of`: Must be a multiple of the specified value.

Example:

```python
from pydantic import conint

age: conint(gt=0, lt=120)
```

### 3. Floats (`confloat`):

Similar to `conint` but for floating point numbers:

- `gt`
- `ge`
- `lt`
- `le`
- `multiple_of`

Example:

```python
from pydantic import confloat

price: confloat(gt=0.0)
```

### 4. Lists (`conlist`):

- `min_items`: Minimum number of items.
- `max_items`: Maximum number of items.

Example:

```python
from pydantic import conlist

numbers: conlist(int, min_items=1, max_items=10)
```

### 5. Others:

- `EmailStr`: Validate string as a valid email address.
- `UrlStr`: Validate string as a valid URL.
- `Hostname`: Validate string as a valid hostname.
- `IPvAnyAddress`: Validate string as a valid IPv4 or IPv6 address.
- `PositiveInt`: Validate as a positive integer.
- `NegativeInt`: Validate as a negative integer.
- `PositiveFloat`: Validate as a positive float.
- `NegativeFloat`: Validate as a negative float.

### 6. Enums:

Enums can be used to limit a value to a specific set of allowed values:

```python
from enum import Enum
from pydantic import BaseModel

class ColorEnum(str, Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"

class Model(BaseModel):
    color: ColorEnum
```

### 7. Validators:

In addition to the above constraints, you can also define custom validation logic using the `@validator` decorator:

```python
from pydantic import BaseModel, validator

class UserModel(BaseModel):
    name: str
    age: int

    @validator('age')
    def check_age(cls, v):
        if v <= 0:
            raise ValueError('Age must be positive')
        return v
```

These are just some of the many constraints and validations that Pydantic offers. For more in-depth details, refer to
    the [official Pydantic documentation](https://pydantic-docs.helpmanual.io/).
"""
import re
from typing import Literal, List

from pydantic import Field, ValidationError, BaseModel

from src.logger import setup_logger

logger = setup_logger(__name__)

from pydantic import constr, validator


class ConStrBase(BaseModel):
    value: str

    min_length: int = 0
    max_length: int = 100
    pattern: str = None
    strip_whitespace: bool = False
    curtail_length: int = None

    @validator("value", pre=True, always=True)
    def apply_constraints(cls, v, values):
        if values.get("strip_whitespace", False):
            v = v.strip()

        if values.get("curtail_length"):
            v = v[:values["curtail_length"]]

        custom_constr = constr(
            min_length=values.get("min_length", 0),
            max_length=values.get("max_length", 100),
            pattern=values.get("pattern", None)
        )

        try:
            value: custom_constr = v
            # return custom_constr.validate(v)
            return value
        except ValidationError:
            raise ValueError(f"Value '{v}' doesn't meet the constraints.")

    def __str__(self):
        return str(self.value)
    def __add__(self, other):
        return str(self.value) + str(other)

    def __mul__(self, times):
        return str(self.value) * times

    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return len(self.value)

    def __contains__(self, item):
        return item in self.value

    def __eq__(self, other):
        if isinstance(other, ConStrBase):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, ConStrBase):
            return self.value < other.value
        return self.value < other

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __hash__(self):
        return hash(self.value)

    class Config:
        extra = "forbid"  # This forbids any additional fields


# Pre-compiled regex patterns
pattern_double_underscores = re.compile(r'^__.*__$')
pattern_id_number = re.compile(r'^__id\d+__$')


class FirestoreIDType(ConStrBase):
    min_length: int = 1
    max_length: int = 100
    pattern: str = None

    @validator("value", pre=True, always=True)
    def apply_firestore_constraints(cls, v):
        try:
            id_str = v.encode('utf-8').decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("The id_str is not a valid UTF-8 string.")

        if len(v.encode('utf-8')) > 1500:
            raise ValueError("The id_str must be no longer than 1,500 bytes.")
        if '/' in v:
            raise ValueError("The id_str cannot contain a forward slash (/).")
        if v in ['.', '..']:
            raise ValueError("The id_str cannot solely consist of a single period (.) or double periods (..).")
        if pattern_double_underscores.match(v):
            raise ValueError("The id_str cannot match the regular expression __.*__.")
        if pattern_id_number.match(v):
            raise ValueError("The id_str cannot match the pattern __id[0-9]+__.")
        return v


class CoreModel(BaseModel):
    """
    Core base model with basic fields and common validation. Models that inherit this class should implement
    their own `set_id` method.

    Attributes
    ----------
    id : str, optional
        The ID of the model instance. By default, it's None.
    status : str, optional
        The status of the model instance, which can be "active", "inactive", or "archived".
        By default, it's "inactive".

    Methods
    -------
    set_id() -> str:
        Abstract method to get the ID of the model instance.
    """
    # This is the parent id field for the model which is used in firestore as their document id
    id: FirestoreIDType = Field(None, hidden=True)  # Hidden from the OPENAPI schema
    status: Literal["active", "inactive", "archived"] = Field("inactive", hidden=True)

    @classmethod
    def __validate_id_field_names(cls):
        for field_name, field_type in cls.__annotations__.items():
            if (field_type == FirestoreIDType and field_name != 'id') and not field_name.endswith('_id'):
                raise ValueError(f"Field {field_name} should end with '_id' since its type is FirestoreIDType.")
            elif field_type == List[FirestoreIDType] and not field_name.endswith('_ids'):
                raise ValueError(f"Field {field_name} should end with '_ids' since its type is List[FirestoreIDType].")

    def __init__(self, **data):
        self.__validate_id_field_names()
        super().__init__(**data)

    class Config:
        """Here so fields can be hidden from the OPENAPI schema if hidden=True. Value can still be used as normal."""

        @staticmethod
        def schema_extra(schema: dict, _):
            props = {}
            for k, v in schema.get('properties', {}).items():
                if not v.get("hidden", False):
                    props[k] = v
            schema["properties"] = props


