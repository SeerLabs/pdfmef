from typing import Optional, List

from pydantic import BaseModel, typing


class Paper(BaseModel):
    id: Optional[str]
    title: Optional[str]
    venue: Optional[str]
    year: Optional[str]
    n_cited_by: Optional[int]
    n_self_cites: Optional[int]
    abstract: str = None
    bibtex: str
    authors: List[str] = []
    journal: str = None
    publish_time: str = None
    source: str
    urls: List[str] = []
    cluster_id: Optional[str]

class Citation(BaseModel):
    id: str
    cluster: Optional[str]
    authors: List[str] = []
    title: Optional[str]
    in_collection: Optional[bool]
    venue: Optional[str]
    venue_type: Optional[str]
    year: Optional[str]
    pages: Optional[str]
    editors: Optional[str]
    publisher: Optional[str]
    pub_address: Optional[str]
    volume: Optional[str]
    number: Optional[str]
    tech: Optional[str]
    raw: Optional[str]
    paper_id: Optional[str]
    self: Optional[str]

class Cluster(BaseModel):
    cluster_id: str
    incollection: int
    cpublisher: Optional[str]
    cyear: Optional[int]
    observations: Optional[str]
    selfCites: Optional[int]
    ctitle: Optional[str]
    ctech: Optional[str]
    cvol: Optional[str]
    cvenue: Optional[str]
    cnum: Optional[int]
    cpages: Optional[str]
    cventype: Optional[str]

class Suggestion(BaseModel):
    type: str
    text: str
    id: str

class AutoCompleteResponse(BaseModel):
    query_id: str
    query: str
    suggestions: List[Suggestion]

class SearchQueryResponse(BaseModel):
    query_id: str
    total_results: int
    response: List[Paper]

class PaperDetailResponse(BaseModel):
    query_id: str
    paper: Paper

class CitationsResponse(BaseModel):
    query_id: str
    total_results: int
    citations: List[Citation]

class SimilarPapersResponse(BaseModel):
    query_id: str
    total_results: int
    similar_papers: List[Citation]

class ClusterDetailResponse(BaseModel):
    query_id: str
    cluster: Cluster

class showCitingClustersResponse(BaseModel):
    query_id: str
    total_results: int
    cluster: Cluster
    papers: List[Paper]

class SearchQuery(BaseModel):
    queryString: str
    page: int
    pageSize: int
