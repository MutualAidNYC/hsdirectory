"""
Taxonomies and Taxonomy Terms API endpoints.

OPTIONAL endpoints per HSDS specification.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from models.hsds import Taxonomy, TaxonomyTerm, Page
from airtable.client import get_airtable_client
from transform.mapper import HSDSMapper

router = APIRouter(tags=["taxonomies"])


# ============================================================================
# Taxonomies
# ============================================================================

@router.get("/taxonomies", response_model=Page)
async def list_taxonomies(
    search: Optional[str] = Query(None, description="Full text search"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    List taxonomies with pagination.
    
    OPTIONAL endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    
    records = await client.list_records("taxonomies")
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        records = [
            r for r in records
            if search_lower in (r.get("fields", {}).get("name", "") or "").lower()
            or search_lower in (r.get("fields", {}).get("description", "") or "").lower()
        ]
    
    taxonomies = [
        mapper.map_taxonomy(r.get("fields", {})).model_dump()
        for r in records
    ]
    
    return mapper.paginate(taxonomies, page, per_page)


@router.get("/taxonomies/{taxonomy_id}", response_model=Taxonomy)
async def get_taxonomy(taxonomy_id: str):
    """
    Get a single taxonomy.
    
    OPTIONAL endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    
    records = await client.list_records(
        "taxonomies",
        filter_formula=f"OR({{id}}='{taxonomy_id}', RECORD_ID()='{taxonomy_id}')"
    )
    
    if not records:
        raise HTTPException(status_code=404, detail="Taxonomy not found")
    
    return mapper.map_taxonomy(records[0].get("fields", {}))


# ============================================================================
# Taxonomy Terms
# ============================================================================

@router.get("/taxonomy_terms", response_model=Page)
async def list_taxonomy_terms(
    search: Optional[str] = Query(None, description="Full text search"),
    taxonomy_id: Optional[str] = Query(None, description="Filter by taxonomy"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    List taxonomy terms with pagination.
    
    OPTIONAL endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    
    # Build filter
    filter_formula = None
    if taxonomy_id:
        filter_formula = f"FIND('{taxonomy_id}', ARRAYJOIN({{taxonomy}}, ',')) > 0"
    
    records = await client.list_records("taxonomy_terms", filter_formula=filter_formula)
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        records = [
            r for r in records
            if search_lower in (r.get("fields", {}).get("name", "") or "").lower()
            or search_lower in (r.get("fields", {}).get("description", "") or "").lower()
        ]
    
    terms = []
    for record in records:
        fields = record.get("fields", {})
        
        # Fetch taxonomy detail
        taxonomy = None
        taxonomy_ids = fields.get("taxonomy", [])
        if taxonomy_ids:
            tax_record = await client.get_record("taxonomies", taxonomy_ids[0])
            if tax_record:
                taxonomy = mapper.map_taxonomy(tax_record.get("fields", {}))
        
        term = mapper.map_taxonomy_term(fields, taxonomy=taxonomy)
        terms.append(term.model_dump())
    
    return mapper.paginate(terms, page, per_page)


@router.get("/taxonomy_terms/{term_id}", response_model=TaxonomyTerm)
async def get_taxonomy_term(term_id: str):
    """
    Get a single taxonomy term.
    
    OPTIONAL endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    
    records = await client.list_records(
        "taxonomy_terms",
        filter_formula=f"OR({{id}}='{term_id}', RECORD_ID()='{term_id}')"
    )
    
    if not records:
        raise HTTPException(status_code=404, detail="Taxonomy term not found")
    
    fields = records[0].get("fields", {})
    
    # Fetch taxonomy detail
    taxonomy = None
    taxonomy_ids = fields.get("taxonomy", [])
    if taxonomy_ids:
        tax_record = await client.get_record("taxonomies", taxonomy_ids[0])
        if tax_record:
            taxonomy = mapper.map_taxonomy(tax_record.get("fields", {}))
    
    return mapper.map_taxonomy_term(fields, taxonomy=taxonomy)
