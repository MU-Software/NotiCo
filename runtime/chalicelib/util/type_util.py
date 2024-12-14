AllowedBasicValueTypes = str | int | float | bool | list | dict | None
ContextType = dict[str, AllowedBasicValueTypes]


def check_classvar_initialized(cls: type, class_vars: list[str]) -> bool:
    if not_initialized_vars := [var for var in class_vars if getattr(cls, var, None) is None]:
        raise TypeError(f"{', '.join(not_initialized_vars)} must be defined in subclass, but {cls.__name__} didn't.")

    return True
