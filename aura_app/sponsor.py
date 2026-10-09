"""Operator-supplied content configuration; no clinical authority is implied.

Content review is the sponsor's responsibility. Invalid resource configuration
retains the accepted built-in fixture fallback instead of hiding safety resources.
"""
from datetime import datetime
import json
import os
from pathlib import Path
from aura_safety.resources import Resource, ResourceBundle, ResourceRegistry, bundle_hash
from aura_communication.domain import ApprovedPolicyQuestion

def resources():
    location=os.environ.get('AURA_SAFETY_RESOURCES')
    if not location:return ResourceRegistry()
    def lookup():
        raw=json.loads(Path(location).read_text())
        if set(raw)!={'version','last_verified','resources'}:raise ValueError('invalid resource bundle')
        rows=tuple(Resource(**row) for row in raw['resources'])
        if not rows or any(not r.resource_id or not r.label or not r.locale for r in rows):raise ValueError('invalid resource content')
        stamp=datetime.fromisoformat(raw['last_verified']) if raw['last_verified'] else None
        if stamp and stamp.tzinfo is None:raise ValueError('resource date requires timezone')
        return ResourceBundle(raw['version'],stamp,rows,bundle_hash(raw['version'],rows))
    return ResourceRegistry(live_lookup=lookup)

def policy_question():
    location=os.environ.get('AURA_POLICY_QUESTION')
    if not location:return None
    raw=json.loads(Path(location).read_text())
    return ApprovedPolicyQuestion(**{**raw,'variants':tuple(raw['variants'])})
