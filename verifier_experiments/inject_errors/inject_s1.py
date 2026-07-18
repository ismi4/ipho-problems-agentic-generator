"""Inject 5 distinct correctness faults into IPhO_2021_S1.pdf (Planetary Physics).

Many targets here are stacked fractions spanning several blocks, so they are
blanked as a region and redrawn as a single linear expression.  Redaction rects
are kept vertically tight: consecutive lines' bounding boxes overlap, and
apply_redactions drops every glyph whose bbox touches the rect.
"""
import fitz
from injlib import Editor

e = Editor("IPhO_2021_S1.pdf")

# --- ERR-6  A.1  faithfulness drift P -> S ------------------------------------
# The problem pours oil "until the LOWER level of the oil has reached the lower
# edges of the plates", giving h' = (rho0/rho_oil) h.  The rewritten solution
# instead assumes the oil surface is level with the water surface (h' = h).  It
# is internally consistent, dimensionally sound, and solves a DIFFERENT problem.
e.blank(0, fitz.Rect(54, 404, 540, 536))
for y, txt in [
    (420, "Let h′ be the height of the column of oil (see Fig. 1). The oil is poured until"),
    (437, "its free surface is level with the water surface, so that h′ = h. Horizontal force"),
    (454, "on the plate is Fx = F1 −F0, where the force due to new fluid is F1 = (ρoil g h′/2)·h′w"),
    (471, "and the force due to water is F0 = (ρ0 g h/2)·hw. Combining all the above, we get"),
]:
    e.draw(0, 56.7, y, txt, 11)
e.draw(0, 239.6, 500, "Fx = (ρoil −ρ0) g h²w / 2 .", 12)
e.draw(0, 56.7, 531, "This force acts on the right plate to the left.", 12)

# --- ERR-7  A.4  wrong retained order in a sanctioned approximation ------------
# D ~ 1/k, so (h+D)^2 is dominated by D^2 ~ k^-2.  Retaining the cross term hD
# ~ k^-1 instead keeps a strictly sub-leading contribution.  The result stays
# dimensionally correct, so only approximation-order reasoning catches it.
e.replace(2, 6, 0, "the term with 𝐷2 ∝𝑘−2", "the term with ℎD ∝k−1")
e.blank(2, fitz.Rect(240, 242, 352, 285))
e.draw(2, 244.7, 262, "F ≈ 2gLh²(ρ1 −ρ0)/k .", 12)

# --- ERR-8  A.5  right-answer-wrong-reasoning (provenance) --------------------
# The stated exponent delta = 3 does not follow from the linear system and
# contradicts the delivered answer tau = A c rho1 D^2 / kappa, which stays
# correct.  Every endpoint check passes; only step-logic re-derivation fails.
e.replace(2, 19, 0, "𝛿= 2", "δ= 3")

# --- ERR-9  B.2  conservation / energy-budget violation -----------------------
# Rays are emitted into a half-plane, i.e. over pi of angle, so the density is
# E/pi.  Normalising over 2pi instead accounts for only E/2 of the released
# energy.  Dimensionally invisible; caught by integrating eps(x) over the surface.
e.blank(4, fitz.Rect(54, 578, 540, 594.8))
e.draw(4, 56.7, 592, "In two dimensions, (E/2π) dθ0 is the energy carried by rays "
                     "emited within [θ0,θ0 + dθ0).", 11)
e.blank(4, fitz.Rect(260, 615, 335, 658))
e.draw(4, 267.5, 640, "ε = (E/2π) |dθ0/dx| .", 12)
e.blank(4, fitz.Rect(205, 734, 390, 775))
e.draw(4, 209.6, 755, "ε(x) = EA / (2πb(A² + x²)) = Ez0 / (π(4z0² + x²))", 12)

# --- ERR-10  B.3  completeness: demanded answer never delivered ---------------
# B.3 asks for x_max "in terms of theta0, delta-theta0 and other constants".
# The closed form is replaced by a promise to evaluate it numerically, so the
# requested quantity is never produced in the demanded form.
e.blank(5, fitz.Rect(210, 688, 385, 732))
e.draw(5, 56.7, 710, "x_max, which can then be evaluated numerically for given θ0 and δθ0.", 11)

e.commit("faulty/IPhO_2021_S1_FAULTY.pdf")
