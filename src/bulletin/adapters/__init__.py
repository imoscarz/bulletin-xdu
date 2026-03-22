from bulletin.adapters.base import BaseAdapter
from bulletin.adapters.dedecms import DedeCMSAdapter
from bulletin.adapters.xidian_cms import XidianCMSAdapter

ADAPTER_REGISTRY: dict[str, type[BaseAdapter]] = {
    "xidian_cms": XidianCMSAdapter,
    "dedecms": DedeCMSAdapter,
}


def get_adapter(adapter_type: str) -> type[BaseAdapter]:
    """Look up an adapter class by its type name."""
    if adapter_type not in ADAPTER_REGISTRY:
        raise ValueError(
            f"Unknown adapter type: {adapter_type!r}. "
            f"Available: {list(ADAPTER_REGISTRY)}"
        )
    return ADAPTER_REGISTRY[adapter_type]
