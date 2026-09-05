# Homework 4 — The Category of Typed Graphs

## Assignment

Prove that graphs typed over a fixed type graph `TG`, together with
type-preserving graph morphisms, form a category.

The solution also proves the supporting result from the lecture slides: the
composition of two graph morphisms is again a graph morphism.

## Main definitions

A directed graph is a tuple

```text
G = (V_G, E_G, s_G, t_G)
```

where `V_G` and `E_G` are the vertex and edge sets, while `s_G` and `t_G`
assign a source and a target to each edge.

A graph morphism `f : G -> H` consists of a vertex function `f_V` and an edge
function `f_E` that preserve incidence:

```text
f_V ∘ s_G = s_H ∘ f_E
f_V ∘ t_G = t_H ∘ f_E
```

A graph typed over the fixed type graph `TG` is a pair `(G, type_G)`, where
`type_G : G -> TG` is a graph morphism.

A morphism between two typed graphs must preserve their typing:

```text
type_H ∘ f = type_G
```

## Proof outline

The proof checks all category requirements:

1. **Closure under composition.** Graph morphisms compose componentwise. If
   `f` and `g` preserve typing, then

   ```text
   type_K ∘ (g ∘ f)
   = (type_K ∘ g) ∘ f
   = type_H ∘ f
   = type_G.
   ```

   Therefore, `g ∘ f` is also type-preserving.

2. **Identity morphisms.** For every typed graph `(G, type_G)`, the ordinary
   identity `id_G` preserves typing because
   `type_G ∘ id_G = type_G`.

3. **Associativity.** Composition is performed through the vertex and edge
   functions, so it inherits associativity from ordinary function
   composition.

4. **Identity laws.** The left and right identity laws are inherited from the
   category of graphs.

Consequently, typed graphs over `TG` and type-preserving graph morphisms form
the slice category commonly written as `Graph/TG` and represented in the
lecture slides as `Graph ↓ TG`.

## Files

```text
Homework4_Matteo_Carrese/
├── README.md
├── STUDY_NOTES_IT.md
└── proof/
    ├── typed_graphs_category.tex
    └── typed_graphs_category.pdf
```

- [`typed_graphs_category.pdf`](proof/typed_graphs_category.pdf) is the final
  proof.
- [`typed_graphs_category.tex`](proof/typed_graphs_category.tex) is the editable
  LaTeX source.

## Build

From the `proof` directory, compile the document twice so that references are
resolved:

```bash
pdflatex typed_graphs_category.tex
pdflatex typed_graphs_category.tex
```

The document uses the `amsmath`, `amsthm`, and `tikz-cd` LaTeX packages.

