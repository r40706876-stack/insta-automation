import os
import json
import time
import re
import subprocess
import asyncio
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts

# =====================================================================
# 1. Configuration & Global Variables
# =====================================================================
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()

GRAPH_API_BASE = "https://graph.facebook.com/v19.0/"
RUPLOAD_BASE = "https://rupload.facebook.com/ig-api-upload/v19.0/"

ASSETS_DIR = "assets/biology_production"
os.makedirs(ASSETS_DIR, exist_ok=True)

FONT_FILE = os.path.join(ASSETS_DIR, "Mukta-Bold.ttf")
FINAL_VIDEO = "biology_auto_reel.mp4"
PROGRESS_FILE = "progress.json"

MALE_VOICE = "hi-IN-MadhurNeural"
FEMALE_VOICE = "hi-IN-SwaraNeural"

RESAMPLE_MODE = getattr(Image, "Resampling", Image).LANCZOS
WHATSAPP_NUMBER = "8989971379"

# =====================================================================
# 2. Universal Phonetic Engine (Dynamic Clean-up for Madhur)
# =====================================================================
class UniversalPhoneticEngine:
    NUM_MAP = {
        "0": "शून्य", "1": "एक", "2": "दो", "3": "तीन", "4": "चार",
        "5": "पांच", "6": "छह", "7": "सात", "8": "आठ", "9": "नौ",
        "10": "दस", "11": "ग्यारह", "12": "बारह", "13": "तेरह",
        "14": "चौदह", "15": "पंद्रह", "16": "सोलह", "17": "सत्रह",
        "18": "अठारह", "19": "उन्नीस", "20": "बीस", "70S": "सत्तर एस",
        "80S": "अस्सी एस", "95%": "पचानवे प्रतिशत", "90%": "नब्बे प्रतिशत"
    }

    # Universal patterns jo Madhur ko atakne nahi dete
    SUBSTITUTIONS = {
        r"\bप्रश्न\b": "सवाल",
        r"\bप्रश्नों\b": "सवालों",
        r"\bद्विगुणन\b": "कॉपी बनने",
        r"\bकोशिकांगों\b": "कोशिका अंगों",
        r"\bकोशिकांग\b": "कोशिका अंग",
        r"\bसमसूत्री\b": "सम सूत्री",
        r"\bअर्धसूत्री\b": "अर्ध सूत्री",
        r"\bगुणसूत्रों\b": "गुण सूत्रों",
        r"\bगुणसूत्र\b": "गुण सूत्र",
        r"\bकायिक\b": "शारीरिक",
        r"\bअगुणित\b": "हाफ",
        r"\bद्विदिशीय\b": "दोनों दिशाओं में",
        r"\bएकदिशीय\b": "एक ही दिशा में",
        r"\bविभज्योतक\b": "मेरिस्टेमैटिक",
        r"\bअवशेषी\b": "बेकार",
        r"\bDNA\b": "डीएनए",
        r"\bRNA\b": "आरएनए",
        r"\bATP\b": "एटीपी",
        r"\bHCl\b": "हाइड्रोक्लोरिक एसिड",
        r"\bS-Phase\b": "एस फेज",
        r"\bS फेज\b": "एस फेज",
        r"\bरील\b": "वीडियो",
        r"\bReel\b": "वीडियो"
    }

    @classmethod
    def sanitize(cls, text):
        # Numbers ko Devnagari words me badalna
        for num, word in cls.NUM_MAP.items():
            text = re.sub(rf"\b{re.escape(num)}\b", word, text)

        # Nukta hatana (Madhur ka slurring rokne ke liye)
        nukta_map = {"ज़": "ज", "फ़": "फ", "क़": "क", "ख़": "ख", "ग़": "ग", "ड़": "ड", "ढ़": "ढ"}
        for k, v in nukta_map.items():
            text = text.replace(k, v)

        # Sanskritized shabdon ka phonetic substitution
        for pattern, replacement in cls.SUBSTITUTIONS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Complex conjuncts simplification
        text = text.replace("ज्ञ", "ग्य")
        text = text.replace("क्ष", "छ")

        # Punctuation aur symbols ko human pauses me badalna
        text = text.replace("!", "।")
        text = text.replace("-", " ")
        text = text.replace("/", " या ")
        text = re.sub(r"[()\[\]]", ", ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

# =====================================================================
# 3. Sequential Topic Database (Auto-Advances Page by Page)
# =====================================================================
TOPICS = [
    {
        "page_no": 5,
        "title": "कोशिका विभाजन (Cell Division)",
        "subtopics": [
            {
                "h1": "1. समसूत्री विभाजन (Mitosis)",
                "badge": "कायिक कोशिकाओं में विभाजन",
                "glow_rgb": (56, 189, 248),
                "points": (
                    "• खोज: वाल्टर फ्लेमिंग ने 1882 में खोज की।\n\n"
                    "• स्थान: शरीर की सभी कायिक कोशिकाओं में होता है।\n\n"
                    "• परिणाम: 1 कोशिका से 2 समान संतति कोशिकाएं।\n\n"
                    "• गुणसूत्र: गुणसूत्रों की संख्या समान बनी रहती है।"
                ),
                "voice": "male",
                "script": "लिख कर ले लो, 2 नंबर का प्रश्न इस रील से पक्का आएगा, चलो देखते हैं। पहली स्लाइड पर देखिए, समसूत्री विभाजन शरीर की मरम्मत और विकास के लिए होता है, जहाँ गुणसूत्रों की संख्या बिल्कुल एक जैसी रहती है।"
            },
            {
                "h1": "2. अर्धसूत्री विभाजन (Meiosis)",
                "badge": "जनन कोशिकाओं में विभाजन",
                "glow_rgb": (16, 185, 129),
                "points": (
                    "• नामकरण: फार्मर तथा मूर ने 1905 में दिया।\n\n"
                    "• स्थान: केवल जनन कोशिकाओं में संपन्न होता है।\n\n"
                    "• परिणाम: 1 कोशिका से 4 अगुणित कोशिकाएं बनती हैं।\n\n"
                    "• क्रॉसिंग ओवर: विभिन्नता के लिए प्रोफ़ेज़ 1 में होता है।"
                ),
                "voice": "female",
                "script": "दूसरी स्लाइड पर ध्यान दीजिए, अर्धसूत्री विभाजन केवल जनन कोशिकाओं में होता है, जिससे बनने वाली चार नई कोशिकाओं में गुणसूत्रों की संख्या आधी रह जाती है।"
            },
            {
                "h1": "3. कोशिका चक्र (Cell Cycle)",
                "badge": "S-Phase DNA Replication",
                "glow_rgb": (244, 63, 94),
                "points": (
                    "• इंटरफेज: कोशिका चक्र का 95% समय इसी में लगता है।\n\n"
                    "• S फेज: DNA का सबसे महत्वपूर्ण द्विगुणन होता है।\n\n"
                    "• G1 व G2: प्रोटीन और कोशिकांगों का निर्माण।\n\n"
                    "• M फेज: वास्तविक विभाजन की सबसे छोटी अवस्था।"
                ),
                "voice": "male",
                "script": "तीसरी स्लाइड पर देखिए, कोशिका चक्र के सबसे मुख्य S फेज के दौरान ही, DNA का द्विगुणन पूरा होता है।"
            }
        ],
        "question": "कोशिका चक्र के किस फेज में DNA का द्विगुणन (Replication) होता है?",
        "options": ["(A) G1 फेज", "(B) S फेज", "(C) G2 फेज", "(D) M फेज"],
        "cta_voice": "female",
        "cta_script": "अब स्क्रीन पर दिख रहे इस सवाल का सही उत्तर जल्दी से कमेंट में लिखकर बताओ। और पूरे सिलेबस के सटीक मॉक टेस्ट और ई-बुक्स के लिए स्क्रीन पर दिए गए नंबर पर अभी व्हाट्सएप करें।",
        "caption": "Biology Cell Division (Mitosis & Meiosis) 🧬📚\n\n• S-Phase, Mitosis & Meiosis Complete Facts.\n• Sahi uttar comment me zaroor likhein!\n• WhatsApp: 8989971379\n\n#BiologyShorts #CellDivision #Mitosis #Meiosis #GovtExamPrep"
    },
    {
        "page_no": 6,
        "title": "पादप ऊतक (Plant Tissues)",
        "subtopics": [
            {
                "h1": "1. विभज्योतक ऊतक (Meristematic)",
                "badge": "निरंतर वृद्धि करने वाले ऊतक",
                "glow_rgb": (34, 197, 94),
                "points": (
                    "• शीर्षस्थ (Apical): जड़ और तने की लंबाई बढ़ाता है।\n\n"
                    "• पार्श्व (Lateral): तने और जड़ की मोटाई बढ़ाता है।\n\n"
                    "• अंतर्वेशी (Intercalary): पत्तियों के आधार में वृद्धि।\n\n"
                    "• विशेषता: इनमें विभाजन की असीम क्षमता होती है।"
                ),
                "voice": "male",
                "script": "लिख कर ले लो, 2 नंबर का प्रश्न इस रील से पक्का आएगा, चलो देखते हैं। पहली स्लाइड पर देखिए, विभज्योतक ऊतक लगातार विभाजित होकर पौधों की लंबाई और तने की मोटाई बढ़ाते हैं।"
            },
            {
                "h1": "2. जाइलम (Xylem Tissue)",
                "badge": "जल संवहन ऊतक",
                "glow_rgb": (14, 165, 233),
                "points": (
                    "• कार्य: जड़ों से पत्तियों तक जल व खनिजों का संवहन।\n\n"
                    "• प्रवाह: जल का प्रवाह केवल ऊपर की ओर (एकदिशीय) होता है।\n\n"
                    "• घटक: ट्रेकिड्स, वाहिकाएं, जाइलम पैरेन्काइमा व फाइबर।\n\n"
                    "• वार्षिक वलय: पेड़ की उम्र जाइलम वलयों से गिनी जाती है।"
                ),
                "voice": "female",
                "script": "दूसरी स्लाइड पर समझिए, जाइलम ऊतक जड़ों से पानी और खनिजों को एक दिशा में प्रवाहित करते हुए पूरे पौधे में ऊपर तक पहुंचाता है।"
            },
            {
                "h1": "3. फ्लोएम (Phloem Tissue)",
                "badge": "भोजन संवहन ऊतक",
                "glow_rgb": (245, 158, 11),
                "points": (
                    "• कार्य: पत्तियों द्वारा बने भोजन का पौधे में संवहन।\n\n"
                    "• प्रवाह: भोजन का प्रवाह द्विदिशीय (ऊपर-नीचे) होता है।\n\n"
                    "• मुख्य कोशिका: चालनी नलिकाएं (Sieve Tubes)।\n\n"
                    "• साथी कोशिकाएं: फ्लोएम संवहन में ऊर्जा प्रदान करती हैं।"
                ),
                "voice": "male",
                "script": "तीसरी स्लाइड पर देखिए, फ्लोएम ऊतक पत्तियों द्वारा तैयार भोजन को पौधे के सभी अंगों तक ऊपर और नीचे दोनों तरफ पहुंचाता है।"
            }
        ],
        "question": "पौधों में जल और खनिजों का संवहन किस ऊतक द्वारा होता है?",
        "options": ["(A) जाइलम", "(B) फ्लोएम", "(C) पैरेन्काइमा", "(D) कोलेंकाइमा"],
        "cta_voice": "female",
        "cta_script": "अब स्क्रीन पर दिख रहे इस सवाल का सही उत्तर तुरंत कमेंट बॉक्स में लिखकर बताओ। और पूरे नोट्स व टेस्ट सीरीज के लिए स्क्रीन पर दिए नंबर पर व्हाट्सएप करें।",
        "caption": "Plant Tissues (Xylem & Phloem) 🌿📚\n\n• Meristematic, Xylem & Phloem High-Yield Facts.\n• Sahi uttar comment me zaroor likhein!\n• WhatsApp: 8989971379\n\n#BiologyShorts #PlantTissues #Xylem #Phloem #GovtExamPrep"
    },
    {
        "page_no": 7,
        "title": "मानव पाचन तंत्र (Digestive System)",
        "subtopics": [
            {
                "h1": "1. मुखगुहा व आमाशय (Mouth & Stomach)",
                "badge": "प्रारंभिक पाचन क्रिया",
                "glow_rgb": (239, 68, 68),
                "points": (
                    "• लार एंजाइम: टायलिन स्टार्च को माल्टोज में बदलता है।\n\n"
                    "• आमाशय में HCl: जीवाणुओं को नष्ट कर माध्यम अम्लीय बनाता है।\n\n"
                    "• पेप्सिन एंजाइम: प्रोटीन को पेप्टोन में तोड़ता है।\n\n"
                    "• रेनिन: दूध के प्रोटीन (कैसीन) का पाचन करता है।"
                ),
                "voice": "male",
                "script": "लिख कर ले लो, 2 नंबर का प्रश्न इस रील से पक्का आएगा, चलो देखते हैं। पहली स्लाइड पर देखिए, मुंह में टायलिन एंजाइम स्टार्च को पचाता है, और पेट में एसिड प्रोटीन को पचाना शुरू करता है।"
            },
            {
                "h1": "2. यकृत व अग्न्याशय (Liver & Pancreas)",
                "badge": "प्रमुख पाचक ग्रंथियां",
                "glow_rgb": (16, 185, 129),
                "points": (
                    "• यकृत (Liver): शरीर की सबसे बड़ी ग्रंथि, पित्त रस बनाती है।\n\n"
                    "• पित्ताशय: पित्त रस का भंडारण और वसा का इमल्सीकरण।\n\n"
                    "• अग्न्याशय: पूर्ण पाचक रस (ट्रिप्सिन, लाइपेज) छोड़ता है।\n\n"
                    "• इंसुलिन: रक्त में ग्लूकोज के स्तर को नियंत्रित करता है।"
                ),
                "voice": "female",
                "script": "दूसरी स्लाइड पर समझिए, शरीर की सबसे बड़ी ग्रंथि यकृत पित्त रस बनाती है, जबकि अग्न्याशय भोजन पचाने के लिए पाचक रस छोड़ता है।"
            },
            {
                "h1": "3. छोटी व बड़ी आंत (Intestines)",
                "badge": "पूर्ण पाचन व अवशोषण",
                "glow_rgb": (56, 189, 248),
                "points": (
                    "• छोटी आंत: भोजन का पूर्ण पाचन और अवशोषण यहीं होता है।\n\n"
                    "• विली (Villi): अवशोषण सतह को कई गुना बढ़ा देती हैं।\n\n"
                    "• बड़ी आंत: केवल अतिरिक्त जल और खनिजों का अवशोषण।\n\n"
                    "• अपेंडिक्स: बड़ी आंत से जुड़ा एक अवशेषी अंग है।"
                ),
                "voice": "male",
                "script": "तीसरी स्लाइड पर देखिए, छोटी आंत में भोजन का पूरा पाचन होता है, और विली द्वारा सभी जरूरी पोषक तत्वों को सोख लिया जाता है।"
            }
        ],
        "question": "मानव शरीर में भोजन का पूर्ण पाचन और अवशोषण कहां होता है?",
        "options": ["(A) आमाशय", "(B) छोटी आंत", "(C) बड़ी आंत", "(D) यकृत"],
        "cta_voice": "female",
        "cta_script": "अब आज के इस एग्जाम चैलेंज का सही उत्तर कमेंट में तुरंत लिखकर बताओ। और पूरे सिलेबस के ई-बुक्स व टेस्ट पेपर्स के लिए स्क्रीन पर दिए गए नंबर पर व्हाट्सएप करें।",
        "caption": "Human Digestive System Complete Revision 🧬🍽️\n\n• Mouth, Liver, Pancreas & Intestine Facts.\n• Sahi uttar comment me zaroor likhein!\n• WhatsApp: 8989971379\n\n#BiologyShorts #DigestiveSystem #HumanPhysiology #GovtExamPrep"
    }
]

def get_current_topic():
    current_idx = 0
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                data = json.load(f)
                current_idx = data.get("current_index", 0)
        except Exception:
            current_idx = 0

    topic = TOPICS[current_idx % len(TOPICS)]
    next_idx = (current_idx + 1) % len(TOPICS)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"current_index": next_idx, "last_posted_page": topic["page_no"]}, f)

    return topic

# =====================================================================
# 4. Font Engine
# =====================================================================
def get_verified_font(size):
    if not os.path.exists(FONT_FILE) or os.path.getsize(FONT_FILE) < 50000:
        font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/mukta/Mukta-Bold.ttf"
        try:
            r = requests.get(font_url, timeout=30)
            if r.status_code == 200:
                with open(FONT_FILE, "wb") as f:
                    f.write(r.content)
        except Exception:
            pass

    try:
        return ImageFont.truetype(FONT_FILE, size)
    except Exception:
        return ImageFont.load_default()

# =====================================================================
# 5. Art & Slide Generator
# =====================================================================
def render_artistic_card(page_no, sub_idx):
    img = Image.new("RGBA", (720, 520), (10, 15, 30, 255))
    d = ImageDraw.Draw(img)

    if page_no == 5:
        if sub_idx == 0:
            d.ellipse([140, 100, 360, 420], fill="#0284c7", outline="#38bdf8", width=5)
            d.ellipse([360, 100, 580, 420], fill="#0284c7", outline="#38bdf8", width=5)
            d.line([(360, 100), (360, 420)], fill="#fde047", width=6)
            d.text((170, 25), "माइटोसिस: 2 समान संतति कोशिकाएं", fill="#bae6fd", font=get_verified_font(26))
        elif sub_idx == 1:
            for cx, cy in [(220, 180), (460, 180), (220, 350), (460, 350)]:
                d.ellipse([cx - 80, cy - 70, cx + 80, cy + 70], fill="#047857", outline="#34d399", width=4)
            d.text((180, 25), "मियोसिस: 4 अगुणित कोशिकाएं", fill="#a7f3d0", font=get_verified_font(26))
        else:
            d.ellipse([160, 80, 560, 440], fill="#312e81", outline="#818cf8", width=6)
            d.arc([180, 100, 540, 420], start=30, end=150, fill="#f43f5e", width=16)
            d.text((220, 25), "कोशिका चक्र: S-Phase (DNA कॉपी)", fill="#fbcfe8", font=get_verified_font(25))
    elif page_no == 6:
        if sub_idx == 0:
            d.rounded_rectangle([100, 80, 620, 440], radius=30, fill="#14532d", outline="#22c55e", width=12)
            d.text((160, 25), "विभज्योतक ऊतक (Meristematic)", fill="#bbf7d0", font=get_verified_font(26))
        elif sub_idx == 1:
            d.rounded_rectangle([120, 90, 600, 430], radius=25, fill="#0c4a6e", outline="#38bdf8", width=6)
            for y in range(130, 400, 30):
                d.line([(200, y), (520, y)], fill="#7dd3fc", width=8)
            d.text((180, 25), "जाइलम: एकदिशीय जल संवहन", fill="#bae6fd", font=get_verified_font(26))
        else:
            d.rounded_rectangle([120, 90, 600, 430], radius=25, fill="#78350f", outline="#f59e0b", width=6)
            d.text((180, 25), "फ्लोएम: द्विदिशीय भोजन संवहन", fill="#fde68a", font=get_verified_font(26))
    else:
        if sub_idx == 0:
            d.ellipse([180, 90, 540, 430], fill="#831843", outline="#f43f5e", width=6)
            d.text((190, 25), "आमाशय: HCl एवं पेप्सिन पाचन", fill="#fbcfe8", font=get_verified_font(26))
        elif sub_idx == 1:
            d.polygon([(160, 380), (360, 110), (560, 380)], fill="#78350f", outline="#f59e0b")
            d.text((190, 25), "यकृत (Liver) एवं अग्न्याशय", fill="#fde68a", font=get_verified_font(26))
        else:
            d.rounded_rectangle([100, 100, 620, 420], radius=40, fill="#064e3b", outline="#10b981", width=6)
            d.text((190, 25), "छोटी आंत: पूर्ण पाचन व विली", fill="#a7f3d0", font=get_verified_font(26))

    return img

def paste_smooth_glow_asset(canvas, asset_img, target_box, glow_rgb):
    x1, y1, x2, y2 = target_box
    w, h = x2 - x1, y2 - y1

    src = asset_img.copy()
    src.thumbnail((w - 40, h - 40), RESAMPLE_MODE)

    mask = Image.new("L", src.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([(0, 0), src.size], radius=22, fill=255)
    src.putalpha(mask)

    px = x1 + (w - src.width) // 2
    py = y1 + (h - src.height) // 2

    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([px - 35, py - 25, px + src.width + 35, py + src.height + 25], fill=(*glow_rgb, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=30))
    canvas.paste(glow, (0, 0), glow)

    canvas.paste(src, (px, py), src)

def draw_base_scaffold(draw, slide_idx, page_no, total=4):
    draw.rounded_rectangle([35, 35, 1045, 1885], radius=28, fill="#070B14", outline="#38BDF8", width=3)
    
    draw.rounded_rectangle([75, 70, 640, 145], radius=14, fill="#F59E0B")
    draw.text((95, 88), f"BIOLOGY REVISION - PAGE {page_no}", fill="#000000", font=get_verified_font(28))
    draw.text((730, 88), f"PART {slide_idx}/4", fill="#38BDF8", font=get_verified_font(30))

    bar_w = int(900 * (slide_idx / total))
    draw.rounded_rectangle([90, 165, 990, 177], radius=6, fill="#1E293B")
    draw.rounded_rectangle([90, 165, 90 + bar_w, 177], radius=6, fill="#38BDF8")

    if slide_idx == 4:
        draw.rounded_rectangle([75, 1715, 1005, 1835], radius=18, fill="#059669")
        draw.text((95, 1748), f"WhatsApp: {WHATSAPP_NUMBER}", fill="#FFFFFF", font=get_verified_font(34))
    else:
        draw.rounded_rectangle([75, 1715, 1005, 1835], radius=18, fill="#1E293B")
        draw.text((150, 1748), "परीक्षा के महत्वपूर्ण बिंदु", fill="#94A3B8", font=get_verified_font(30))

def generate_slides_for_topic(topic):
    slide_files = []
    f_h1 = get_verified_font(46)
    f_badge = get_verified_font(28)
    f_body = get_verified_font(34)
    f_label = get_verified_font(30)
    page_no = topic["page_no"]

    for idx, sub in enumerate(topic["subtopics"]):
        img = Image.new("RGB", (1080, 1920), color="#020617")
        d = ImageDraw.Draw(img)
        draw_base_scaffold(d, idx + 1, page_no)

        title_color = "#38BDF8" if idx == 0 else ("#10B981" if idx == 1 else "#F43F5E")
        d.text((75, 205), sub["h1"], fill=title_color, font=f_h1)

        box = [75, 280, 1005, 830]
        d.rounded_rectangle(box, radius=22, fill="#0B132B", outline=title_color, width=2)
        card_art = render_artistic_card(page_no, idx)
        paste_smooth_glow_asset(img, card_art, box, sub["glow_rgb"])

        d.rounded_rectangle([95, 300, 600, 360], radius=10, fill="#1E293B")
        d.text((115, 312), sub["badge"], fill="#F8FAFC", font=f_badge)

        d.rounded_rectangle([75, 855, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
        d.text((105, 885), "परीक्षा के महत्वपूर्ण बिंदु:", fill="#FBBF24", font=f_label)
        d.multiline_text((105, 955), sub["points"], fill="#F8FAFC", font=f_body, spacing=16)

        slide_path = f"slide_{idx+1}.png"
        img.save(slide_path)
        slide_files.append(slide_path)

    # Slide 4: Interactive Quiz & CTA
    img4 = Image.new("RGB", (1080, 1920), color="#020617")
    d4 = ImageDraw.Draw(img4)
    draw_base_scaffold(d4, 4, page_no)
    d4.text((75, 205), "कमेंट में सही उत्तर दें!", fill="#FBBF24", font=f_h1)

    d4.rounded_rectangle([75, 270, 1005, 560], radius=22, fill="#1E293B", outline="#FBBF24", width=3)
    d4.text((105, 300), "🎯 EXAM CHALLENGE:", fill="#FBBF24", font=f_label)
    d4.multiline_text((105, 365), textwrap.fill(topic["question"], width=26), fill="#FFFFFF", font=f_body, spacing=10)

    qy = 600
    for opt in topic["options"]:
        d4.rounded_rectangle([75, qy, 1005, qy + 95], radius=14, fill="#0F172A", outline="#38BDF8", width=2)
        d4.text((110, qy + 25), opt, fill="#F8FAFC", font=f_body)
        qy += 115

    pdf_box = [75, 1140, 1005, 1680]
    d4.rounded_rectangle(pdf_box, radius=22, fill="#111827", outline="#10B981", width=2)
    d4.text((120, 1200), "📚 COMPLETE BIOLOGY NOTES", fill="#34D399", font=f_label)
    hint_desc = (
        "• सही उत्तर कमेंट में लिखें!\n\n"
        f"• WhatsApp: {WHATSAPP_NUMBER}\n\n"
        "• सम्पूर्ण नोट्स और टेस्ट के लिए मैसेज करें!"
    )
    d4.multiline_text((120, 1280), hint_desc, fill="#F8FAFC", font=get_verified_font(28), spacing=12)

    s4_path = "slide_4.png"
    img4.save(s4_path)
    slide_files.append(s4_path)

    return slide_files

# =====================================================================
# 6. Audio Generation Engine (Automated Madhur Interceptor)
# =====================================================================
async def generate_audio_clip(text, voice, filename):
    if voice == MALE_VOICE:
        clean_text = UniversalPhoneticEngine.sanitize(text)
        comm = edge_tts.Communicate(text=clean_text, voice=voice, rate="-4%", pitch="+2Hz")
    else:
        comm = edge_tts.Communicate(text=text, voice=voice, rate="+0%", pitch="+0Hz")
    await comm.save(filename)

async def make_all_voice_clips(topic):
    audio_files = []
    for i, sub in enumerate(topic["subtopics"]):
        chosen_voice = MALE_VOICE if sub["voice"] == "male" else FEMALE_VOICE
        fn = f"voice_part_{i+1}.mp3"
        await generate_audio_clip(sub["script"], chosen_voice, fn)
        audio_files.append(fn)

    cta_voice = FEMALE_VOICE if topic["cta_voice"] == "female" else MALE_VOICE
    fn_cta = "voice_part_4.mp3"
    await generate_audio_clip(topic["cta_script"], cta_voice, fn_cta)
    audio_files.append(fn_cta)

    return audio_files

def compile_alternate_video(slide_files, audio_files, output_file):
    durations = []
    for af in audio_files:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", af]
        dur = float(subprocess.check_output(cmd).decode().strip())
        durations.append(dur)

    total_dur = sum(durations)
    target_dur = 58.5
    speed_factor = round(total_dur / target_dur, 3)

    balanced_audios = []
    balanced_durations = []
    for i, af in enumerate(audio_files):
        out_af = f"balanced_{af}"
        subprocess.run(["ffmpeg", "-y", "-i", af, "-filter:a", f"atempo={speed_factor}", out_af], check=True)
        balanced_audios.append(out_af)
        b_dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", out_af]).decode().strip())
        balanced_durations.append(b_dur)

    with open("audio_list.txt", "w") as f:
        for b_af in balanced_audios:
            f.write(f"file '{b_af}'\n")

    combined_audio = "combined_voice.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", combined_audio], check=True)
    final_audio_dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", combined_audio]).decode().strip())

    inputs = []
    filter_complex = ""
    for idx, s_path in enumerate(slide_files):
        inputs.extend(["-i", s_path])
        filter_complex += f"[{idx}:v]loop=loop=-1:size=1:start=0,trim=duration={balanced_durations[idx]},setpts=PTS-STARTPTS[v{idx}]; "

    concat_inputs = "".join([f"[v{i}]" for i in range(len(slide_files))])
    filter_complex += f"{concat_inputs}concat=n={len(slide_files)}:v=1:a=0,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p[vout]"

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", combined_audio,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{len(slide_files)}:a",
        "-t", f"{final_audio_dur:.2f}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"\n🎬 100% Synchronized Video Ready: {output_file}\n")

# =====================================================================
# 7. Instagram Upload Engine
# =====================================================================
def post_reel_to_instagram_multipart(video_file, caption):
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("Notice: Token ya ID missing hai. Video locally ready hai.")
        return

    print("🚀 Instagram auto-upload start ho raha hai...")
    init_url = f"{GRAPH_API_BASE}{IG_USER_ID}/media"
    data = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    r = requests.post(init_url, data=data, timeout=60).json()
    video_id = r.get("id")
    upload_url = r.get("uri") or f"{RUPLOAD_BASE}{video_id}"

    time.sleep(10)
    file_size = os.path.getsize(video_file)
    headers = {
        "Authorization": f"OAuth {IG_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size),
        "Content-Type": "application/octet-stream"
    }

    with open(video_file, "rb") as vf:
        video_bytes = vf.read()

    requests.post(upload_url, headers=headers, data=video_bytes, timeout=600)

    status_url = f"{GRAPH_API_BASE}{video_id}"
    for _ in range(35):
        time.sleep(12)
        res = requests.get(status_url, params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN}).json()
        if res.get("status_code") == "FINISHED":
            break

    pub_url = f"{GRAPH_API_BASE}{IG_USER_ID}/media_publish"
    pub_res = requests.post(pub_url, data={"creation_id": video_id, "access_token": IG_ACCESS_TOKEN}).json()
    if "id" in pub_res:
        print(f"🎉 SUCCESS! Reel Live on Instagram! ID: {pub_res['id']}")

# =====================================================================
# 8. Main Execution Pipeline
# =====================================================================
if __name__ == "__main__":
    current_topic = get_current_topic()
    print(f"\n=======================================================")
    print(f"🎯 Auto-Posting: Page {current_topic['page_no']} - {current_topic['title']}")
    print(f"=======================================================\n", flush=True)

    print("Step 1: 4 Slides generate ho rahi hain...", flush=True)
    slides = generate_slides_for_topic(current_topic)

    print("Step 2: Male (Madhur 99% Fix) & Female Voiceovers generate ho rahe hain...", flush=True)
    audio_clips = asyncio.run(make_all_voice_clips(current_topic))

    print("Step 3: FFmpeg dwara 58.5s exact audio-visual sync chal raha hai...", flush=True)
    compile_alternate_video(slides, audio_clips, FINAL_VIDEO)

    print("Step 4: Instagram auto-upload execute ho raha hai...", flush=True)
    post_reel_to_instagram_multipart(FINAL_VIDEO, current_topic["caption"])
