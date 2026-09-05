"""Generate the AGG grammar used by Homework 5.

The script deliberately uses only Python's standard library.  It produces the
XML-based ``.ggx`` format understood by AGG and keeps all identifiers unique.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "agg" / "UCD2CD_TGG.ggx"


@dataclass
class IdFactory:
    value: int = 0

    def new(self) -> str:
        self.value += 1
        return f"I{self.value}"


ids = IdFactory()


def element(parent: ET.Element, tag: str, **attributes: str) -> ET.Element:
    return ET.SubElement(parent, tag, attributes)


def add_layout(node: ET.Element, x: int, y: int) -> None:
    element(node, "NodeLayout", X=str(x), Y=str(y))


def add_edge_layout(edge: ET.Element) -> None:
    element(edge, "EdgeLayout", bendX="0", bendY="0", textOffsetX="0", textOffsetY="-18")


def add_node(
    graph: ET.Element,
    type_id: str,
    x: int,
    y: int,
    *,
    attribute_type: str | None = None,
    value: str | None = None,
    variable: bool = False,
) -> str:
    node_id = ids.new()
    node = element(graph, "Node", ID=node_id, type=type_id)
    if attribute_type is not None and value is not None:
        attribute_flags = {"variable": "true"} if variable else {"constant": "true"}
        attribute = element(node, "Attribute", type=attribute_type, **attribute_flags)
        value_element = element(attribute, "Value")
        element(value_element, "string").text = value
    add_layout(node, x, y)
    return node_id


def add_edge(graph: ET.Element, type_id: str, source: str, target: str) -> str:
    edge_id = ids.new()
    edge = element(graph, "Edge", ID=edge_id, source=source, target=target, type=type_id)
    add_edge_layout(edge)
    return edge_id


def add_mapping(morphism: ET.Element, original: str, image: str) -> None:
    element(morphism, "Mapping", orig=original, image=image)


document = ET.Element("Document", version="1.0")
system = element(
    document,
    "GraphTransformationSystem",
    ID=ids.new(),
    directed="true",
    name="UCD2CD_TGG_Matteo_Carrese",
    parallel="false",
)

handler = element(system, "TaggedValue", Tag="AttrHandler", TagValue="Java Expr")
element(handler, "TaggedValue", Tag="Package", TagValue="java.lang")
for tag, value in (
    ("CSP", "true"),
    ("injective", "true"),
    ("dangling", "true"),
    ("identification", "true"),
    ("NACs", "true"),
    ("layered", "true"),
    ("breakAllLayer", "true"),
    ("showGraphAfterStep", "true"),
    ("TypeGraphLevel", "ENABLED"),
):
    element(system, "TaggedValue", Tag=tag, TagValue=value)

types = element(system, "Types")


def node_type(name: str, colour: str, shape: str = "RECT", named: bool = False) -> tuple[str, str | None]:
    type_id = ids.new()
    node = element(
        types,
        "NodeType",
        ID=type_id,
        abstract="false",
        name=f"{name}%:{shape}:{colour}:[NODE]:",
    )
    if not named:
        return type_id, None
    attribute_id = ids.new()
    element(node, "AttrType", ID=attribute_id, attrname="name", typename="String", visible="true")
    return type_id, attribute_id


def edge_type(name: str, colour: str, style: str = "SOLID_LINE") -> str:
    type_id = ids.new()
    element(
        types,
        "EdgeType",
        ID=type_id,
        abstract="false",
        name=f"{name}%:{style}:{colour}:[EDGE]:",
    )
    return type_id


SOURCE = "java.awt.Color[r=190,g=45,b=45]"
CORRESPONDENCE = "java.awt.Color[r=210,g=150,b=0]"
TARGET = "java.awt.Color[r=35,g=85,b=190]"

actor_type, actor_name = node_type("Actor", SOURCE, named=True)
use_case_type, use_case_name = node_type("UseCase", SOURCE, named=True)
actor_to_class_type, _ = node_type("Actor2Class", CORRESPONDENCE, shape="OVAL")
use_case_to_operation_type, _ = node_type("UseCase2Operation", CORRESPONDENCE, shape="OVAL")
association_to_ownership_type, _ = node_type("Association2Ownership", CORRESPONDENCE, shape="OVAL")
class_type, class_name = node_type("Class", TARGET, shape="ROUNDRECT", named=True)
operation_type, operation_name = node_type("Operation", TARGET, shape="ROUNDRECT", named=True)

participates_type = edge_type("participates", SOURCE)
source_actor_type = edge_type("sourceActor", CORRESPONDENCE, "DASHED_LINE")
source_use_case_type = edge_type("sourceUseCase", CORRESPONDENCE, "DASHED_LINE")
target_class_type = edge_type("targetClass", CORRESPONDENCE, "DASHED_LINE")
target_operation_type = edge_type("targetOperation", CORRESPONDENCE, "DASHED_LINE")
owns_type = edge_type("owns", TARGET)

type_graph = element(types, "Graph", ID=ids.new(), kind="TG", name="UCD2CD_Triple_Type_Graph")
tg_actor = add_node(type_graph, actor_type, 70, 90)
tg_use_case = add_node(type_graph, use_case_type, 70, 270)
tg_a2c = add_node(type_graph, actor_to_class_type, 330, 70)
tg_uc2o = add_node(type_graph, use_case_to_operation_type, 330, 230)
tg_assoc = add_node(type_graph, association_to_ownership_type, 330, 390)
tg_class = add_node(type_graph, class_type, 650, 90)
tg_operation = add_node(type_graph, operation_type, 650, 270)
add_edge(type_graph, participates_type, tg_actor, tg_use_case)
add_edge(type_graph, source_actor_type, tg_a2c, tg_actor)
add_edge(type_graph, target_class_type, tg_a2c, tg_class)
add_edge(type_graph, source_use_case_type, tg_uc2o, tg_use_case)
add_edge(type_graph, target_operation_type, tg_uc2o, tg_operation)
add_edge(type_graph, source_actor_type, tg_assoc, tg_actor)
add_edge(type_graph, source_use_case_type, tg_assoc, tg_use_case)
add_edge(type_graph, target_class_type, tg_assoc, tg_class)
add_edge(type_graph, target_operation_type, tg_assoc, tg_operation)
add_edge(type_graph, owns_type, tg_class, tg_operation)

# A small source model is embedded as the initial host graph.  The rules add
# correspondence and target elements without changing these source nodes.
host = element(system, "Graph", ID=ids.new(), kind="HOST", name="OnlineShop_UseCase_Model")
customer = add_node(host, actor_type, 80, 80, attribute_type=actor_name, value="Customer")
administrator = add_node(host, actor_type, 80, 260, attribute_type=actor_name, value="Administrator")
browse = add_node(host, use_case_type, 350, 40, attribute_type=use_case_name, value="Browse catalog")
order = add_node(host, use_case_type, 350, 130, attribute_type=use_case_name, value="Place order")
manage = add_node(host, use_case_type, 350, 270, attribute_type=use_case_name, value="Manage catalog")
add_edge(host, participates_type, customer, browse)
add_edge(host, participates_type, customer, order)
add_edge(host, participates_type, administrator, manage)


def new_rule(name: str, layer: int, parameters: tuple[str, ...]) -> tuple[ET.Element, ET.Element, ET.Element]:
    rule = element(system, "Rule", ID=ids.new(), formula="true", name=name)
    for parameter in parameters:
        element(rule, "Parameter", name=parameter, type="String")
    lhs = element(rule, "Graph", ID=ids.new(), kind="LHS", name=f"LHS_{name}")
    rhs = element(rule, "Graph", ID=ids.new(), kind="RHS", name=f"RHS_{name}")
    return rule, lhs, rhs


def finish_rule(
    rule: ET.Element,
    name: str,
    mappings: list[tuple[str, str]],
    nac_graph: ET.Element,
    nac_mappings: list[tuple[str, str]],
    layer: int,
) -> None:
    morphism = element(rule, "Morphism", name=name)
    for original, image in mappings:
        add_mapping(morphism, original, image)
    conditions = element(rule, "ApplCondition")
    nac = element(conditions, "NAC")
    nac.append(nac_graph)
    nac_morphism = element(nac, "Morphism", name=f"NAC_{name}")
    for original, image in nac_mappings:
        add_mapping(nac_morphism, original, image)
    element(rule, "TaggedValue", Tag="layer", TagValue=str(layer))
    element(rule, "TaggedValue", Tag="priority", TagValue="0")


# Rule 1: one target Class and one trace node for each source Actor.
rule, lhs, rhs = new_rule("ActorToClass", 0, ("actorName",))
l_actor = add_node(lhs, actor_type, 70, 90, attribute_type=actor_name, value="actorName", variable=True)
r_actor = add_node(rhs, actor_type, 70, 90, attribute_type=actor_name, value="actorName", variable=True)
r_trace = add_node(rhs, actor_to_class_type, 320, 90)
r_class = add_node(rhs, class_type, 600, 90, attribute_type=class_name, value="actorName", variable=True)
add_edge(rhs, source_actor_type, r_trace, r_actor)
add_edge(rhs, target_class_type, r_trace, r_class)
nac_graph = ET.Element("Graph", ID=ids.new(), kind="NAC", name="NAC_ActorAlreadyMapped")
n_actor = add_node(nac_graph, actor_type, 70, 90, attribute_type=actor_name, value="actorName", variable=True)
n_trace = add_node(nac_graph, actor_to_class_type, 320, 90)
add_edge(nac_graph, source_actor_type, n_trace, n_actor)
finish_rule(rule, "ActorToClass", [(l_actor, r_actor)], nac_graph, [(l_actor, n_actor)], 0)

# Rule 2: one target Operation and one trace node for each source UseCase.
rule, lhs, rhs = new_rule("UseCaseToOperation", 1, ("useCaseName",))
l_use_case = add_node(lhs, use_case_type, 70, 90, attribute_type=use_case_name, value="useCaseName", variable=True)
r_use_case = add_node(rhs, use_case_type, 70, 90, attribute_type=use_case_name, value="useCaseName", variable=True)
r_trace = add_node(rhs, use_case_to_operation_type, 320, 90)
r_operation = add_node(rhs, operation_type, 600, 90, attribute_type=operation_name, value="useCaseName", variable=True)
add_edge(rhs, source_use_case_type, r_trace, r_use_case)
add_edge(rhs, target_operation_type, r_trace, r_operation)
nac_graph = ET.Element("Graph", ID=ids.new(), kind="NAC", name="NAC_UseCaseAlreadyMapped")
n_use_case = add_node(nac_graph, use_case_type, 70, 90, attribute_type=use_case_name, value="useCaseName", variable=True)
n_trace = add_node(nac_graph, use_case_to_operation_type, 320, 90)
add_edge(nac_graph, source_use_case_type, n_trace, n_use_case)
finish_rule(rule, "UseCaseToOperation", [(l_use_case, r_use_case)], nac_graph, [(l_use_case, n_use_case)], 1)

# Rule 3: an Actor--UseCase relation becomes Class--Operation ownership.
rule, lhs, rhs = new_rule("AssociationToOwnership", 2, ("actorName", "useCaseName"))
l_actor = add_node(lhs, actor_type, 60, 70, attribute_type=actor_name, value="actorName", variable=True)
l_use_case = add_node(lhs, use_case_type, 60, 240, attribute_type=use_case_name, value="useCaseName", variable=True)
l_class = add_node(lhs, class_type, 650, 70, attribute_type=class_name, value="actorName", variable=True)
l_operation = add_node(lhs, operation_type, 650, 240, attribute_type=operation_name, value="useCaseName", variable=True)
l_a2c = add_node(lhs, actor_to_class_type, 340, 70)
l_uc2o = add_node(lhs, use_case_to_operation_type, 340, 240)
l_participates = add_edge(lhs, participates_type, l_actor, l_use_case)
l_a2c_src = add_edge(lhs, source_actor_type, l_a2c, l_actor)
l_a2c_trg = add_edge(lhs, target_class_type, l_a2c, l_class)
l_uc2o_src = add_edge(lhs, source_use_case_type, l_uc2o, l_use_case)
l_uc2o_trg = add_edge(lhs, target_operation_type, l_uc2o, l_operation)

r_actor = add_node(rhs, actor_type, 60, 70, attribute_type=actor_name, value="actorName", variable=True)
r_use_case = add_node(rhs, use_case_type, 60, 240, attribute_type=use_case_name, value="useCaseName", variable=True)
r_class = add_node(rhs, class_type, 650, 70, attribute_type=class_name, value="actorName", variable=True)
r_operation = add_node(rhs, operation_type, 650, 240, attribute_type=operation_name, value="useCaseName", variable=True)
r_a2c = add_node(rhs, actor_to_class_type, 340, 70)
r_uc2o = add_node(rhs, use_case_to_operation_type, 340, 240)
r_relation_trace = add_node(rhs, association_to_ownership_type, 340, 390)
r_participates = add_edge(rhs, participates_type, r_actor, r_use_case)
r_a2c_src = add_edge(rhs, source_actor_type, r_a2c, r_actor)
r_a2c_trg = add_edge(rhs, target_class_type, r_a2c, r_class)
r_uc2o_src = add_edge(rhs, source_use_case_type, r_uc2o, r_use_case)
r_uc2o_trg = add_edge(rhs, target_operation_type, r_uc2o, r_operation)
add_edge(rhs, source_actor_type, r_relation_trace, r_actor)
add_edge(rhs, source_use_case_type, r_relation_trace, r_use_case)
add_edge(rhs, target_class_type, r_relation_trace, r_class)
add_edge(rhs, target_operation_type, r_relation_trace, r_operation)
add_edge(rhs, owns_type, r_class, r_operation)

nac_graph = ET.Element("Graph", ID=ids.new(), kind="NAC", name="NAC_AssociationAlreadyMapped")
n_actor = add_node(nac_graph, actor_type, 60, 70, attribute_type=actor_name, value="actorName", variable=True)
n_use_case = add_node(nac_graph, use_case_type, 60, 240, attribute_type=use_case_name, value="useCaseName", variable=True)
n_class = add_node(nac_graph, class_type, 650, 70, attribute_type=class_name, value="actorName", variable=True)
n_operation = add_node(nac_graph, operation_type, 650, 240, attribute_type=operation_name, value="useCaseName", variable=True)
n_a2c = add_node(nac_graph, actor_to_class_type, 340, 70)
n_uc2o = add_node(nac_graph, use_case_to_operation_type, 340, 240)
n_relation_trace = add_node(nac_graph, association_to_ownership_type, 340, 390)
n_participates = add_edge(nac_graph, participates_type, n_actor, n_use_case)
n_a2c_src = add_edge(nac_graph, source_actor_type, n_a2c, n_actor)
n_a2c_trg = add_edge(nac_graph, target_class_type, n_a2c, n_class)
n_uc2o_src = add_edge(nac_graph, source_use_case_type, n_uc2o, n_use_case)
n_uc2o_trg = add_edge(nac_graph, target_operation_type, n_uc2o, n_operation)
add_edge(nac_graph, source_actor_type, n_relation_trace, n_actor)
add_edge(nac_graph, source_use_case_type, n_relation_trace, n_use_case)

lhs_to_rhs = [
    (l_actor, r_actor),
    (l_use_case, r_use_case),
    (l_class, r_class),
    (l_operation, r_operation),
    (l_a2c, r_a2c),
    (l_uc2o, r_uc2o),
    (l_participates, r_participates),
    (l_a2c_src, r_a2c_src),
    (l_a2c_trg, r_a2c_trg),
    (l_uc2o_src, r_uc2o_src),
    (l_uc2o_trg, r_uc2o_trg),
]
lhs_to_nac = [
    (l_actor, n_actor),
    (l_use_case, n_use_case),
    (l_class, n_class),
    (l_operation, n_operation),
    (l_a2c, n_a2c),
    (l_uc2o, n_uc2o),
    (l_participates, n_participates),
    (l_a2c_src, n_a2c_src),
    (l_a2c_trg, n_a2c_trg),
    (l_uc2o_src, n_uc2o_src),
    (l_uc2o_trg, n_uc2o_trg),
]
finish_rule(rule, "AssociationToOwnership", lhs_to_rhs, nac_graph, lhs_to_nac, 2)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
rough_xml = ET.tostring(document, encoding="utf-8", xml_declaration=True)
pretty_xml = minidom.parseString(rough_xml).toprettyxml(indent="  ", encoding="UTF-8")
OUTPUT.write_bytes(pretty_xml)
print(OUTPUT)
