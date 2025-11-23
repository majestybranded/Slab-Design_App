import math
import streamlit as st

def check_span_limits(spans):
    for i in range(1, len(spans)):
        diff = abs(spans[i] - spans[i - 1])
        if diff > 0.2 * min(spans[i], spans[i - 1]):
            st.error(f"❌ Span difference between Span {i} and {i + 1} is more than 20% of the shorter span.")
            return False
    return True

def check_load_ratio(dead, live):
    if dead == 0:
        st.error("❌ Dead load cannot be zero.")
        return False
    if live / dead >= 3:
        st.error("❌ Live load / Dead load ratio must be less than 3.")
        return False
    return True


def slab_thickness(spans):
    max_L = max(spans)

    # End span: L/24, Interior span: L/28
    t1 = max(max_L * 12 / 24, max_L * 12 / 28)

    # Round up to the nearest multiple of 3
    t = math.ceil(t1 / 3) * 3

    return t


def self_weight_slab(t_in):
    weight_conc = 150  # pcf
    t_ft = t_in / 12
    return round(weight_conc * t_ft, 2)


def ultimate_load(dead, self_wt, live):
    total_dead = dead + self_wt
    # ACI Load Combination: 1.2 * Dead + 1.6 * Live
    wu = (1.2 * total_dead + 1.6 * live) / 1000  # Convert to ksf
    return total_dead, wu


def round_sig(x, sig=3):
    if x == 0:
        return 0
    return float(f"{x:.{sig}g}")


def design_moments(spans, wu):
    # Using ACI 318-19 Moment Coefficients
    M = []
    n = len(spans)

    # ACI coefficients require 2 or more spans
    if n == 2:
        # Special case for 2 spans
        for L in spans:
            Mu = wu * L ** 2
            M.append({
                'Moment at A': round_sig((1 / 24) * Mu),
                'Moment at B': round_sig((1 / 14) * Mu),
                'Moment at C': round_sig((1 / 9) * Mu),
            })
    else:
        # 3 or more spans
        for i, L in enumerate(spans):
            Mu = wu * L ** 2
            if i == 0:
                M.append({
                    'Moment at A': round_sig((1 / 24) * Mu),
                    'Moment at B': round_sig((1 / 14) * Mu),
                    'Moment at C': round_sig((1 / 10) * Mu),
                 })
            elif i == n - 1:

                if spans[0] == spans[-1]:
                    M.append(M[0])
                else:
                    M.append({
                        'Moment at A': round_sig((1 / 24) * Mu),
                        'Moment at B': round_sig((1 / 14) * Mu),
                        'Moment at C': round_sig((1 / 10) * Mu),

                    })
            else:  # Interior spans
                M.append({
                    'Moment at C': round_sig((1 / 10) * Mu),
                    'Moment at D': round_sig((1 / 16) * Mu),
                    'Moment at E': round_sig((1 / 11) * Mu),

                })
    return M

def reinforcement_design(M_list, t_in, fc, fy, bar_size):
    b = 12
    d = t_in - 1
    phi = 0.9

    dia = bar_size / 8
    bar_area = (math.pi / 4) * (dia ** 2)

    shrink_bar_area = 0.11  # For #3 bar
    shrink_spacing_limit = (5 * t)

    results = []

    for span in M_list:
        span_result = {}
        for key, Mu in span.items():
            Mu_inlb = Mu * 12
            Ru = Mu_inlb / (b * d ** 2)  # Ru in psi

            # Convert fc and fy from ksi to psi
            fc_psi = fc * 1000
            fy_psi = fy * 1000

            term = (2 * Ru) / (0.85 * phi * fc)
            rho = (0.85 * phi * fc / fy) * (1 - math.sqrt(1 - term))

            As = rho * b * d
            As_min_temp_shrink = 0.0018 * b * t_in

            #for Area of Steel final
            As_final = max(As, As_min_temp_shrink)

            spacing1 = (bar_area / As_final) * 12  # theoretical spacing
            spacing_limit = 2 * t_in  # ACI max spacing = 2 × thickness

            if spacing1 > spacing_limit:
                spacing = spacing_limit
                spacing_note = f"(limited to 2×t = {spacing_limit:.0f} in)"
            else:
                spacing = spacing1
                spacing_note = ""

            # ✅ Round down main bar spacing to nearest whole number
            spacing = round(spacing)

            # Shrinkage Bar Calculations (Perpendicular reinforcement)
            As_shrink = 0.5 * As_min_temp_shrink
            shrink_spacing = ((0.11 / As_shrink) * 12)
            shrink_spacing = min(shrink_spacing, shrink_spacing_limit)

            # ✅ Round down shrinkage spacing to nearest whole number
            shrink_spacing = math.floor(shrink_spacing)

            span_result[key] = {
                'Mu (kip-ft)': round_sig(Mu),
                'Ru (ksi)': round_sig(Ru),
                'ρ (rho)': round_sig(rho, 4),
                'As_req (in²/ft)': round_sig(As, 3),
                'As_min (in²/ft)': round_sig(As_min_temp_shrink, 3),
                'As_final (in²/ft)': round_sig(As_final, 3),
                'Bar #': f"#{int(bar_size)}",
                'Spacing (Main)': f"@ {spacing} in C/C",
                'Shrinkage Bar': f"#3 @ {shrink_spacing} in C/C"
            }
        results.append(span_result)
    return results



                                              # WEB APP



st.title(" 𝙾𝚗𝚎-𝙴𝚗𝚍 𝙲𝚘𝚗𝚝𝚒𝚗𝚞𝚘𝚞𝚜 𝚂𝚕𝚊𝚋 𝙳𝚎𝚜𝚒𝚐𝚗 𝚃𝚘𝚘𝚕:")
st.write("𝕋𝕙𝕚𝕤 𝕥𝕠𝕠𝕝 𝕡𝕖𝕣𝕗𝕠𝕣𝕞𝕤 𝕡𝕣𝕖𝕝𝕚𝕞𝕚𝕟𝕒𝕣𝕪 𝕕𝕖𝕤𝕚𝕘𝕟 𝕠𝕗 𝕠𝕟𝕖-𝕨𝕒𝕪 𝕤𝕝𝕒𝕓 𝕓𝕒𝕤𝕖𝕕 𝕠𝕟 𝔸ℂ𝕀-𝟛𝟙𝟡.")
st.write("𝙶𝚛𝚘𝚞𝚙 𝙼𝚎𝚖𝚋𝚎𝚛𝚜:")
st.write("𝖮𝗄𝖺𝗌𝗁𝖺 𝖪𝖺𝗆𝗋𝖺𝗇(𝖢𝖤-181), 𝖠𝖻𝖽𝗎𝗅 𝖲𝖺𝗆𝖺𝖽(𝖢𝖤-194), 𝖬𝖺𝗇𝗂𝖺 𝖲𝗂𝖽𝖽𝗂𝗊𝗎𝗂(𝖢𝖤-204), 𝖠𝖺𝗂𝗌𝗁𝖺 𝖹𝗎𝗅𝖿𝗂𝗊𝖺𝗋(𝖢𝖤-309)")
# Sidebar UI (Inputs ke liye)
st.sidebar.header("Design Inputs")

st.sidebar.subheader("Loads & Materials")
dead_load = st.sidebar.number_input("Dead Load (psf) (excluding slab self-weight)", min_value=0.0, value=20.0, step=5.0)
live_load = st.sidebar.number_input("Live Load (psf)", min_value=0.0, value=40.0, step=10.0)
fc = st.sidebar.number_input("Concrete Strength f'c (ksi)", min_value=3.0, value=4.0, step=0.5)
fy = st.sidebar.number_input("Steel Yield Strength fy (ksi)", min_value=40.0, value=60.0, step=10.0)
bar_size = st.sidebar.selectbox("Main Bar Size (#)", [3, 4, 5, 6, 7, 8], index=1)  # Default #4 bar

st.sidebar.subheader("No of Bar & Span Length")
num_spans = st.sidebar.number_input("Number of spans (minimum 2)", min_value=2, value=3, step=1)

spans = []
for i in range(num_spans):
    L = st.sidebar.number_input(f"Clear Span Length {i + 1} (ft)", min_value=1.0, value=15.0, step=1.0, key=f"span_{i}")
    spans.append(L)

# Calculate Button
if st.sidebar.button("Calculate Design", type="primary"):

    st.header("Design Calculation Results")

    # --- 1. Validation Checks ---
    if check_span_limits(spans) and check_load_ratio(dead_load, live_load):

        st.info("✅ All input checks passed.")

        # --- 2. Slab Thickness & Loads ---
        st.subheader("1. Slab Thickness & Loads")
        t = slab_thickness(spans)
        self_wt = self_weight_slab(t)
        total_dead, wu = ultimate_load(dead_load, self_wt, live_load)

        st.success(f"**Calculated Slab Thickness (t): {t} in**")
        st.write(f"Slab Self-weight: {self_wt} psf")
        st.write(f"Total Dead Load (Dead + Self-wt): {total_dead:.2f} psf")
        st.write(f"**Ultimate Factored Load (Wu): {wu:.3f} ksf**")

        # --- 3. Design Moments ---
        st.subheader("2. Design Moments (kip-ft / ft)")
        M = design_moments(spans, wu)

        # Display moments in a cleaner way
        for i, m_dict in enumerate(M):
            st.write(f"**Span {i + 1} (L = {spans[i]} ft):**")


        # --- 4. Reinforcement Design ---
        st.subheader("3. Reinforcement Design")
        As_results = reinforcement_design(M, t, fc, fy, bar_size)

        for i, res_dict in enumerate(As_results):
            st.write(f"**Span {i + 1} Reinforcement:**")
            st.dataframe(res_dict)
            st.write("---")  # Separator

else:

    st.info("𝙴𝚗𝚝𝚎𝚛 𝚢𝚘𝚞𝚛 𝚍𝚎𝚜𝚒𝚐𝚗 𝚙𝚊𝚛𝚊𝚖𝚎𝚝𝚎𝚛𝚜 𝚒𝚗 𝚝𝚑𝚎 𝚜𝚒𝚍𝚎𝚋𝚊𝚛 𝚊𝚗𝚍 𝚌𝚕𝚒𝚌𝚔 '𝙲𝚊𝚕𝚌𝚞𝚕𝚊𝚝𝚎 𝙳𝚎𝚜𝚒𝚐𝚗'.")

