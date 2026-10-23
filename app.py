import streamlit as st
from pathlib import Path
from rag import PlantRAG, load_documents
from research import search_pubmed

ROOT = Path(__file__).parent
st.set_page_config(page_title="Know Your Plant", page_icon="🌱", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600&display=swap');
:root { --green:#245b43; --leaf:#63845a; --cream:#f6f5ed; }
.stApp { background: var(--cream); }
h1,h2,h3 { font-family:'Playfair Display', Georgia, serif !important; }
.hero { padding: 1.5rem 0 .5rem; }
.eyebrow { text-transform:uppercase; letter-spacing:.18em; font-size:.72rem; color:#63845a; font-weight:700; }
.small-note { color:#687568; font-size:.86rem; }
.source-card { border:1px solid #dfe5d8; border-radius:12px; padding:12px; margin:.4rem 0; background:#fffef9; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_rag():
    docs = load_documents(ROOT / "data" / "plant_knowledge.json")
    return PlantRAG(docs)

rag = get_rag()

with st.sidebar:
    st.markdown("## 🌱 Know Your Plant")
    st.caption("Know the plant, not just the brand.")
    audience = st.radio("Explanation style", ["Curious kid", "Deep dive"], horizontal=False)
    st.divider()
    st.markdown("### Explore")
    selected_plant = st.selectbox("Choose a plant", ["Neem", "Holy basil", "Turmeric", "Banyan", "Red mangrove", "Sunflower", "Aloe vera", "Rice"])
    st.markdown("---")
    st.caption("Learning resource only. Plant uses are not medical advice.")

st.markdown('<div class="hero"><div class="eyebrow">A little wonder grows everywhere</div><h1>Know the plant. <span style="color:#63845a">Know its world.</span></h1><p>Discover where plants come from, how climate shapes them, what people use them for, and what scientists are investigating.</p></div>', unsafe_allow_html=True)

tab_discover, tab_ask, tab_research, tab_method = st.tabs(["🌿 Discover", "💬 Ask Plant AI", "🔬 Research watch", "🧪 How it works"])

plants = {
    "Neem": ("Azadirachta indica", "🌳", "Warm regions · tree", "A tree with a long relationship with people across South Asia. Its story connects ecology, agriculture, culture and scientific investigation."),
    "Holy basil": ("Ocimum tenuiflorum", "🌿", "Warm regions · herb", "A fragrant herb linking gardens, food, cultural traditions and research into plant chemistry."),
    "Turmeric": ("Curcuma longa", "🫚", "Humid tropics · rhizome", "A golden rhizome with a complex cultivation history and an evolving research literature."),
    "Banyan": ("Ficus benghalensis", "🌳", "Tropical South Asia · tree", "A tree that can become an entire habitat, connecting branches, roots, figs and wildlife."),
    "Red mangrove": ("Rhizophora mangle", "🌱", "Tropical coastlines · tree", "A coastal specialist shaped by tidal flooding, salty conditions and oxygen-poor sediments."),
    "Sunflower": ("Helianthus annuus", "🌻", "Temperate to warm · crop", "A familiar flower with a deep domestication story and an important role in food systems."),
    "Aloe vera": ("Aloe vera", "🪴", "Dry climates · succulent", "A water-storing succulent and a useful example of why product claims and plant parts matter."),
    "Rice": ("Oryza sativa", "🌾", "Warm growing seasons · crop", "A staple crop whose varieties and farming systems connect plants, people, water and climate.")
}

with tab_discover:
    p = plants[selected_plant]
    left, right = st.columns([1, 2])
    with left:
        st.markdown(f"<div style='background:#e5eedc;border-radius:24px;padding:2rem;text-align:center;font-size:5rem'>{p[1]}</div>", unsafe_allow_html=True)
        st.caption(p[2])
    with right:
        st.markdown(f"## {selected_plant}")
        st.markdown(f"*{p[0]}*")
        st.write(p[3])
        st.markdown("#### Explore its story")
        st.write("Origin and range · climate and habitat · human and ecological uses · research and evidence")
        if st.button(f"Ask a question about {selected_plant}", key="discover_ask"):
            st.session_state["question"] = f"Explain the origin, climate adaptations and uses of {selected_plant}."
            st.session_state["go_ask"] = True
    st.info("This starter knowledge base is intentionally small. Add reviewed, licensed source documents before presenting it as a comprehensive botanical reference.")

with tab_ask:
    st.markdown("## Ask Plant AI")
    st.write("Answers are grounded in retrieved documents. Each source includes its title, source URL and a document identifier.")
    default_q = st.session_state.pop("question", "")
    question = st.text_input("What are you curious about?", value=default_q, placeholder="Why does neem grow well in seasonal dry climates?")
    if st.button("Find evidence and answer", type="primary") and question.strip():
        with st.spinner("Retrieving relevant plant knowledge…"):
            result = rag.answer(question, audience=audience)
        st.markdown("### Answer")
        st.write(result["answer"])
        if result.get("mode") == "evidence_only":
            st.caption("No language-model API key was found. This response is an evidence-led excerpt, not a generated synthesis.")
        st.markdown("### Evidence used")
        for i, source in enumerate(result["sources"], 1):
            with st.expander(f"{i}. {source['title']} · relevance {source['score']:.2f}"):
                st.write(source["excerpt"])
                st.markdown(f"[Open source]({source['source_url']})")
                st.caption(f"Document ID: {source['doc_id']} · Section: {source.get('section','general')}")
        if not result["sources"]:
            st.warning("I couldn't find enough evidence in the current knowledge base. Try a different question or add a reliable source document.")
    if st.session_state.pop("go_ask", False):
        st.caption("Your selected plant question is ready above.")

with tab_research:
    st.markdown("## Research watch")
    st.write("Search PubMed for recent scientific literature. Search results are publications to inspect—not automatic proof that a claim is true.")
    plant_for_research = st.selectbox("Research topic", list(plants.keys()), index=list(plants.keys()).index(selected_plant), key="research_plant")
    query = st.text_input("Optional search refinement", value="climate OR ecology OR phytochemistry", help="Combine a plant name with a narrower research question.")
    if st.button("Search PubMed"):
        search_term = f'"{plants[plant_for_research][0]}" AND ({query})'
        with st.spinner("Searching PubMed…"):
            try:
                results = search_pubmed(search_term, limit=8)
                if not results:
                    st.info("No results returned. Try a broader query.")
                for item in results:
                    st.markdown(f"**[{item['title']}]({item['url']})**")
                    st.caption(f"{item.get('year','Year unavailable')} · PMID {item['pmid']}")
                    st.write(item.get("abstract","No abstract available from the API."))
                    st.divider()
            except Exception as exc:
                st.error(f"Research search could not complete: {exc}")
                st.caption("Check internet access and the NCBI API status, then retry.")
    st.caption("Research metadata via NCBI PubMed E-utilities. Respect NCBI usage guidance and cite the original publication.")

with tab_method:
    st.markdown("## How the RAG pipeline works")
    st.code("Question → retrieve relevant chunks → score evidence → generate a grounded answer → validate citations → show sources", language="text")
    st.markdown("### Current implementation")
    st.write("- Local TF-IDF retrieval baseline; no embedding API is required.")
    st.write("- Optional OpenAI generation when `OPENAI_API_KEY` is configured.")
    st.write("- If no key is available, return a clearly labelled evidence-only response.")
    st.write("- Chunk-level source metadata is attached before retrieval and rendered from the source records—not invented by the model.")
    st.write("- A separate evaluation script tests retrieval quality, citation validity and abstention behaviour.")
    st.markdown("### Source strategy")
    st.write("Use curated botanical references for taxonomy and range, biodiversity occurrence records for observations, and PubMed for research discovery. Never treat an occurrence point as proof of a species' complete native range.")
    st.markdown("### Safety boundary")
    st.write("Traditional uses and laboratory findings are described as such. The app does not diagnose, prescribe, or recommend eating or applying a plant. Toxicity and preparation can vary by species and plant part.")

st.markdown("---")
st.caption("Know Your Plant · educational prototype · verify botanical claims against the cited source before relying on them.")
