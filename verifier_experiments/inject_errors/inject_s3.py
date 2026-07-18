"""Inject 5 distinct correctness faults into IPhO_2023_S3.pdf (Water and Objects).

Two constraints shape how edits are written:
  * every `replace` must match CONTIGUOUS characters -- the matched chars' bboxes
    are unioned into one redaction rect, so a split match would erase the text
    lying between the two halves;
  * replacement text must stay in the Basic Multilingual Plane.  PyMuPDF emits a
    broken ToUnicode CMap for U+1D400-block math italics, so 'x' is used where
    the surrounding document has U+1D465.  Semantics are unaffected.
"""
import fitz
from injlib import Editor

e = Editor("IPhO_2023_S3.pdf")

# --- ERR-1  A.1  dimensionless geometric factor: 2^(2/3) -> 2^(1/3) -----------
# Merging two radius-a drops gives R = 2^(1/3) a, so the merged surface AREA
# carries 2^(2/3).  Substituting 2^(1/3) is invisible to dimensional analysis and
# still yields a plausible, correctly-united speed.
e.replace(0, 7, 0, "2/3", "1/3", size=7)            # (S3.2)
e.replace(0, 12, 1, "2/3", "1/3", size=7)           # (S3.4) first radical
e.replace(0, 13, 0, "2/3", "1/3", size=7)           # (S3.4) second radical
e.replace(0, 13, 2, "0.23\x012", "0.311")           # propagated numeric
e.replace(0, 15, 2, "0.23", "0.31")                 # boxed answer

# --- ERR-2  B.3  sign / direction flip ---------------------------------------
# Correct balance is f_x + gamma cos(t2) - gamma cos(t1) = 0.  All three lines of
# B.3 flip together, so the sub-part stays internally coherent but is wrong.
# The whole term is rewritten as one contiguous span.  Swapping just the two
# subscript glyphs in place leaves them geometrically detached from their
# symbols, which scrambles reading order; blanking the entire line is also
# unsafe here because consecutive lines' bounding boxes overlap vertically.
e.replace(1, 14, 0, "𝛾cos 𝜃2 −𝛾cos 𝜃1", "γcos θ1 −γcos θ2")   # prose statement
e.replace(1, 15, 0, "𝛾cos 𝜃2 −𝛾cos 𝜃1", "γcos θ1 −γcos θ2")   # (S3.6)
e.replace(1, 16, 2, "𝛾cos 𝜃1 −𝛾cos 𝜃2", "γcos θ2 −γcos θ1")   # boxed answer

# --- ERR-3  B.4  dimensional inconsistency: l = sqrt(gamma/rho g) -> sqrt(gamma/rho)
# gamma/rho = m^3/s^2, so the root has dimension m^1.5/s and cannot be a length.
e.replace(1, 27, 0, "𝑔", "")                        # inline
e.replace(2, 4, 0, "𝑔", "")                         # boxed answer

# --- ERR-4  B.5  wrong boundary-condition branch ------------------------------
# Retains the growing exponential: claims z(inf)=0 forces B=0, then A = +l tan(t0),
# giving z = l tan(t0) e^{+x/l}, which diverges instead of decaying.
e.replace(2, 19, 0, "𝐴", "B")                       # "leads to A = 0" -> B = 0
e.replace(2, 20, 0, "𝐵", "A")                       # "leads to B ="  -> A =
e.replace(2, 20, 0, "= −ℓtan", "= ℓtan")            # drop the minus sign
e.replace(2, 21, 2, "= −ℓtan", "= ℓtan")            # boxed answer
e.replace(2, 21, 2, "−𝑥/ℓ", "x/ℓ", size=7)          # exponent becomes +x/l

# --- ERR-5  C.2  demanded-form / symbol-whitelist violation -------------------
# C.2 requires F_x "without using theta_a, theta_b, z_a, z_b".  The expression
# below is algebraically CORRECT (z_0 substituted from C.3) but re-introduces
# z_a and x_a, so it fails the answer-form check and nothing else.
e.blank(4, fitz.Rect(87, 193, 180, 224))
e.draw(4, 89.2, 211.5, "Fx = −2ρg za² / (e^(xa/ℓ) + e^(−xa/ℓ))²", 10)

e.commit("faulty/IPhO_2023_S3_FAULTY.pdf")
