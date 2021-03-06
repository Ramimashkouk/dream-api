from neomodel import db, config, clear_neo4j_database
from settings import OntologySettings
import querymaker


def drop_database():
    clear_neo4j_database(db)


def create_kind_node(kind: str, node_dict: dict):
    """Create new node

    :param kind: node kind
    :param node_dict: node params
    :return:
    """
    query = querymaker.merge_node_query(kind, node_dict)
    db.cypher_query(query, node_dict)


def search_nodes(kind: str, node_dict: Optional[dict] = None, limit=10) -> list:
    """Search existing nodes

    :param kind: node kind
    :param node_dict: node params
    :param limit: maximum # nodes returned
    :return: neo4j nodes list
    """
    if node_dict is None:
        node_dict = {}
    match_a, filter_a = querymaker.match_node_query("a", kind, node_dict)
    return_ = f"RETURN a\n LIMIT {limit}"
    query = "\n".join([match_a, return_])

    nodes, _ = db.cypher_query(query, filter_a)
    return nodes


def update_node(kind: str, updates: dict, filter_node: Optional[dict] = None):
    """Update a node properties

    :param kind: node kind
    :param filter_node: node match filter
    :param updates: new properties and updated properties
    :return:
    """
    if filter_node is None:
        filter_node = {}
    nodes = search_nodes(kind, filter_node)
    if len(nodes)==1: # we need to update exactly one node
        match_node, filter_node = querymaker.match_node_query("a", kind, filter_node)
        set_query, updated_updates = querymaker.set_property_query("a", updates)
        params = {**filter_node, **updated_updates}
        query = "\n".join([match_node, set_query])
        db.cypher_query(query, params)


def delete_node(kind: str, node_dict: dict, completely=False):
    """Delete a node completely from database or make it in the past
    :param kind: node kind
    :param node_dict: node params
    :param completely: if True, then the node will be deleted completely
                        from DB with all its relationships
    """
    if completely:
        match_a, filter_a = querymaker.match_node_query("a", kind, node_dict)
        delete_a = querymaker.delete_query("a")

        query = "\n".join([match_a, delete_a])
        params = filter_a

        db.cypher_query(query, params)
        return


def create_relationship(
    kind_a: str,
    filter_a: dict,
    relationship: str,
    rel_dict: dict,
    kind_b: str,
    filter_b: dict,
):
    """Find nodes A and B and set a relationship between them

    :param kind_a: node A kind
    :param filter_a: node A match filter
    :param relationship: relationship between nodes A and B
    :param kind_b: node B kind
    :param filter_b: node B match filter
    :return:
    """
    match_a, filter_a = querymaker.match_node_query("a", kind_a, filter_a)
    match_b, filter_b = querymaker.match_node_query("b", kind_b, filter_b)
    rel = querymaker.merge_relationship_query("a", relationship, rel_dict, "b")

    query = "\n".join([match_a, match_b, rel])
    params = {**filter_a, **filter_b, **rel_dict}

    db.cypher_query(query, params)


def search_relationships(
    relationship: str,
    filter_dict: Optional[dict] = None,
    kind_a: str = "",
    filter_a: Optional[dict] = None,
    kind_b: str = "",
    filter_b: Optional[dict] = None,
    limit=10,
    programmer=0,
) -> list:
    """Search existing relationships

    :param relationship: relationship type
    :param filter_dict: relationship params
    :param kind_a: node A kind
    :param filter_a: node A match filter
    :param kind_b: node B kind
    :param filter_b: node B match filter
    :param limit: maximum # nodes returned
    :param programmer: False for returning the relationship found.
                        True for returning query, params of matching that relationship.
    :return: neo4j relationships list
    """
    if filter_dict is None:
        filter_dict = {}
    if filter_a is None:
        filter_a = {}
    if filter_b is None:
        filter_b = {}
    node_a_query, node_b_query = [""] * 2
    if kind_a:
        node_a_query, filter_a = querymaker.match_node_query("a", kind_a, filter_a)
    if kind_b:
        node_b_query, filter_b = querymaker.match_node_query("b", kind_b, filter_b)
    rel_query, filter_dict = querymaker.match_relationship_query(
        "a", "r", relationship, filter_dict, "b"
    )
    return_ = f"RETURN a, r, b\nLIMIT {limit}"

    query = "\n".join([node_a_query, node_b_query, rel_query, return_])
    params = {**filter_a, **filter_b, **filter_dict}

    if programmer:
        query = "\n".join([node_a_query, node_b_query, rel_query])
        return query, params

    rels, _ = db.cypher_query(query, params)
    return rels


def update_relationship(
    relationship: str,
    updates: dict,
    filter_rel: dict = None,
    kind_a: str = "",
    filter_a: dict = None,
    kind_b: str = "",
    filter_b: dict = None,
):
    """Update a relationship properties

    :param relationship: relationship type
    :param updates: new properties and updated properties
    :param filter_rel: relationship params
    :param kind_a: node A kind
    :param filter_a: node A match filter
    :param kind_b: node B kind
    :param filter_b: node B match filter
    :return:
    """
    filter_rel = filter_rel or {}
    filter_a = filter_a or {}
    filter_b = filter_b or {}
    match_relationship, params = search_relationships(
        relationship, filter_rel, kind_a, filter_a, kind_b, filter_b, programmer=1
    )
    set_query, updated_updates = querymaker.set_property_query("r", updates)
    query = "\n".join([match_relationship, set_query])
    params = {**params, **updated_updates}
    db.cypher_query(query, params)


def delete_relationship(
    relationship: str,
    filter_rel: Optional[dict] = None,
    kind_a: str = "",
    filter_a: Optional[dict] = None,
    kind_b: str = "",
    filter_b: Optional[dict] = None,
):
    """Delete a relationship between two nodes A and B
    :param relationship: relationship type
    :param filter_rel: relationship params
    :param kind_a: node A kind
    :param filter_a: node A match filter
    :param kind_b: node B kind
    :param filter_b: node B match filter
    :return:
    """
    if filter_a is None:
        filter_a = {}
    if filter_b is None:
        filter_b = {}
    if filter_rel is None:
        filter_rel = {}
    match_relationship, params = search_relationships(
        relationship, filter_rel, kind_a, filter_a, kind_b, filter_b, programmer=1
    )
    delete_query = querymaker.delete_query("r", node=False)
    query = "\n".join([match_relationship, delete_query])

    db.cypher_query(query, params)


ontology_settings = OntologySettings()

config.DATABASE_URL = ontology_settings.neo4j_bolt_url
