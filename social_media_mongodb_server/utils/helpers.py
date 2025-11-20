from bson import ObjectId
from typing import Any, Dict

def mongo_obj_to_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    if not d:
        return d
    out = dict(d)
    if "_id" in out:
        out["id"] = str(out["_id"])
        out.pop("_id", None)
    return out

def to_object_id(s: str) -> ObjectId:
    try:
        return ObjectId(s)
    except Exception as e:
        raise ValueError("Invalid ObjectId") from e
