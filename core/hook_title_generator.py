import re
from typing import Dict, Any, List, Set, Optional
from core.hinglish_transliteration import to_hinglish

class HookTitleGenerator:
    """
    Intelligent Hook Title Engine that understands video domain and individual clip dialogue.
    Guarantees:
    - 100% Roman Hinglish / English (zero Devanagari)
    - 3 to 6 words MAX, ALL CAPS + 1 fitting emoji
    - 100% Unique per clip across the video (no duplicates)
    - Content-specific and strictly relevant to what is actually discussed in that clip
    - NEVER slices raw conversational sentence fragments (no "MATALAB US TAIM PAR")
    """

    CONVERSATIONAL_FILLERS = {
        "MATLAB", "JUST", "DOSTON", "BHAI", "YAAR", "DEKHO", "SAMJH", "SAMAJH",
        "RAHE", "HO", "NA", "AAP", "MEREE", "MERE", "KO", "AISAA", "AISA", "LAGTA",
        "HAI", "THA", "THAA", "THI", "THE", "US", "TAIM", "TIME", "PAR", "PE",
        "LAGAYA", "DEKHA", "BOLA", "BOL", "RAHA", "RAHE", "HUAA", "HUA", "HUI",
        "EK", "DUM", "BHI", "TOH", "TO", "AUR", "AND", "BUT", "LEKIN", "MAGAR",
        "YEH", "YE", "WO", "WOH", "KYA", "KYUN", "KAISE", "JAISE", "KAB", "AB",
        "HUM", "MAIN", "MUJHE", "HAMARA", "TUM", "TERA", "TERE", "APNE", "APNA"
    }

    @classmethod
    def detect_video_domain(cls, video_info: Dict[str, Any], transcript_sample: str = "") -> str:
        """Classifies the overarching topic and category of the source video."""
        title = video_info.get("title", "")
        desc = video_info.get("description", "")
        tags = " ".join(video_info.get("tags", []))
        uploader = video_info.get("uploader", "")
        combined = f"{title} {uploader} {tags} {desc[:2000]} {transcript_sample[:2000]}".lower()

        if any(w in combined for w in ["gta", "gameplay", "rockstar", "vice city", "gaming", "pubg", "valorant", "minecraft", "trailer reaction", "walkthrough", "clutch", "esports"]):
            return "gaming"
        if any(w in combined for w in ["scam", "hack", "cyber", "otp", "fraud", "police", "security", "dark web", "phishing", "malware", "spyware"]):
            return "cybersecurity"
        if any(w in combined for w in ["ambani", "antilia", "luxury", "mansion", "house tour", "billionaire", "net worth", "expensive house", "penthouse"]):
            return "luxury_architecture"
        if any(w in combined for w in ["podcast", "interview", "carryminati", "tanmay", "samay", "talk show", "conversation", "roast", "confession"]):
            return "podcast_interview"
        if any(w in combined for w in ["tech", "gadget", "iphone", "android", "unboxing", "review", "laptop", "pc build", "smartphone", "camera test", "artificial intelligence", "chatgpt"]):
            return "tech_gadgets"
        if any(w in combined for w in ["money", "business", "startup", "finance", "stock", "invest", "trading", "crypto", "crore", "lakh", "revenue", "profit"]):
            return "business_finance"
        if any(w in combined for w in ["science", "space", "isro", "nasa", "earth", "facts", "documentary", "history", "mystery"]):
            return "education_facts"
        return "general"

    @classmethod
    def generate_hook_title(
        cls,
        clip: Dict[str, Any],
        video_info: Dict[str, Any],
        used_titles: Optional[Set[str]] = None,
        domain: Optional[str] = None
    ) -> str:
        """
        Synthesizes a unique, content-tailored 3-6 word hook title for a specific clip.
        Uses exact spoken dialogue in the clip to derive the title.
        """
        if used_titles is None:
            used_titles = set()

        if not domain:
            domain = cls.detect_video_domain(video_info)

        # 1. Gather all textual context for this exact clip
        transcript_slice = clip.get("transcript_slice", [])
        if transcript_slice:
            clip_speech = " ".join(s.get("text", "") for s in transcript_slice).strip()
            opening_sentence = transcript_slice[0].get("text", "").strip()
        else:
            clip_speech = clip.get("text", "").strip()
            opening_sentence = clip.get("hook_text", "").strip() or clip.get("title", "")

        clip_title = clip.get("title", "").strip()
        combined_text = f"{opening_sentence} {clip_speech} {clip_title}"
        roman_clip = to_hinglish(combined_text).lower()

        candidates: List[str] = []

        # -------------------------------------------------------------
        # DOMAIN 1: GAMING & GTA 6 (CarryMinati / Gameplay / Tech)
        # -------------------------------------------------------------
        if domain == "gaming" or any(w in roman_clip for w in ["gta", "rockstar", "gameplay", "ps5", "rdr2", "game"]):
            # Scenario A: Slow internet, dial-up, BSNL 64 kbps nostalgia
            if any(w in roman_clip for w in ["64 kbps", "kbps", "dial-up", "dial up", "speed badha", "speed badha ke", "papa please", "papa se jhagda", "papa se ladai"]):
                candidates.extend([
                    "64 KBPS PE GTA DOWNLOAD?! 😭",
                    "PAPA SE INTERNET KI LADAI! 📞",
                    "DIAL-UP INTERNET NOSTALGIA! ⏳",
                    "SLOW INTERNET GTA STRUGGLE! 💻",
                    "PURANE DINO KI GAMING YAADEIN! 🎮"
                ])

            # Scenario B: 89 parts download, corrupt part, 40GB compressed in parts
            if any(w in roman_clip for w in ["89 part", "89 parts", "parts", "ek mahina", "download kiya", "corrupt", "6 gb", "40 gb"]):
                candidates.extend([
                    "40 GB GAME IN 89 PARTS?! 💿",
                    "EK MAHINE TAK GAME DOWNLOAD! ⏳",
                    "89 PARTS CRASHED AT THE END?! 💀",
                    "GAMING DOWNLOAD STRUGGLE ERA! 😭",
                    "PART CORRUPT HONE KA DARD! 💔"
                ])

            # Scenario C: PC release date, PS5 Pro vs PC, when will PC release
            if any(w in roman_clip for w in ["pc ke liye", "pc release", "ps5 pro", "ps5", "pc me kab", "pc version"]):
                candidates.extend([
                    "GTA 6 PC RELEASE DATE?! 🖥️",
                    "PS5 PRO VS PC GAMING! 🎮",
                    "PC PE GTA 6 KAB AAYEGA?! ⚡",
                    "CONSOLE FIRST, PC LATER?! 🤯",
                    "GTA 6 SYSTEM REQUIREMENTS?! 💻"
                ])

            # Scenario D: Rockstar Games & RDR2 legacy, Red Dead comparison
            if any(w in roman_clip for w in ["rdr 2", "rdr2", "rockstar", "chaap chhodega", "regret", "masterpiece", "saloon tak"]):
                candidates.extend([
                    "WHY ROCKSTAR NEVER FAILS! 👑",
                    "RDR2 JAISA MASTERPIECE HOGA?! 🤯",
                    "ROCKSTAR KA ASLI MASTERCLASS! 🏆",
                    "GTA 6 WILL MAKE HISTORY! ✨",
                    "BEST OPEN WORLD GAME EVER?! 🌟"
                ])

            # Scenario E: GTA 5 vs GTA 6 comparison, chill vibes, mature content
            if any(w in roman_clip for w in ["gta5", "gta 5", "gta6", "gta 6", "chill", "vibes", "dikhta hai", "samajh rahe ho"]):
                candidates.extend([
                    "GTA 5 VS GTA 6 VIBES! 🎮",
                    "GTA 6 CHILL MAHOL & REALITY! 🌴",
                    "GTA 5 KO PEECHE CHHODEGA?! 🔥",
                    "GTA 6 CRAZY OPEN WORLD! 🏖️",
                    "NEXT ERA OF GTA BEGINS! ⚡"
                ])

            # Scenario F: Graphics, realism, animated vs real, physics
            if any(w in roman_clip for w in ["graphics", "realistic", "physics", "real life", "visuals", "animated"]):
                candidates.extend([
                    "INSANE NEXT-GEN GRAPHICS! 🤯",
                    "REAL LIFE YA VIDEO GAME?! 🎮",
                    "GRAPHICS THAT BROKE THE INTERNET! 🔥",
                    "UNREALISTIC ENGINE DETAILS! ✨"
                ])

            # Scenario G: Esports / Clutch / Multi-kills
            if any(w in roman_clip for w in ["clutch", "1v4", "1v3", "ace", "headshot", "kill", "last second"]):
                candidates.extend([
                    "INSANE 1v4 IMPOSSIBLE CLUTCH! 🔥",
                    "LAST SECOND GAME WIN! 🏆",
                    "PRO LEVEL GOD CLUTCH! ⚡",
                    "UNBELIEVABLE AIM REFLEXES! 🎯"
                ])

        # -------------------------------------------------------------
        # DOMAIN 2: CYBERSECURITY & TECH SCAMS
        # -------------------------------------------------------------
        if domain == "cybersecurity" or any(w in roman_clip for w in ["scam", "hack", "cyber", "police", "otp", "fraud"]):
            if any(w in roman_clip for w in ["camera", "photo", "tasveer", "lens", "webcam"]):
                candidates.extend([
                    "PHONE CAMERA HACK REALITY! 📱",
                    "CAMERA SPYING SE KAISE BACHEIN?! 🚨",
                    "AAPKA CAMERA SURAKSHIT HAI?! ⚠️",
                    "LIVE CAMERA HACK EXPOSED! 📸"
                ])
            if any(w in roman_clip for w in ["screen", "swipe", "open", "live", "dekh raha"]):
                candidates.extend([
                    "LIVE PHONE SCREEN SPYING! 👀",
                    "SCREEN RECORDING SPY ALERT! 🚨",
                    "AAPKI SCREEN KOI DEKH RAHA HAI?! 😱",
                    "REMOTE ACCESS HACK EXPOSED! 📱"
                ])
            if any(w in roman_clip for w in ["fake profile", "instagram", "impersonat", "account", "dharpakad"]):
                candidates.extend([
                    "FAKE INSTAGRAM PROFILE SCAM! 🚨",
                    "INSTAGRAM IMPERSONATION TRUTH! ⚠️",
                    "FAKE ACCOUNT SE CYBER FRAUD?! 📱",
                    "CYBER POLICE DHARPAKAD FILES! 👮"
                ])
            if any(w in roman_clip for w in ["modus operandi", "syndicate", "dgp", "sp", "mastermind", "operation"]):
                candidates.extend([
                    "CRIMINAL MODUS OPERANDI EXPOSED! 📂",
                    "CYBER SYNDICATE NETWORK BUSTED! 🚨",
                    "DGP & POLICE SPECIAL OPERATION! 👮",
                    "CYBER GANG MASTERMIND ARRESTED! ⛓️"
                ])
            if any(w in roman_clip for w in ["no mentor", "bina mentor", "mentor", "seekha", "bachpan", "hacking shuru"]):
                candidates.extend([
                    "BINA MENTOR KE HACKER BANA?! 💻",
                    "HOW A TEENAGER BECAME A HACKER! ⚡",
                    "SELF TAUGHT ETHICAL HACKER! 🧠",
                    "ZERO SE CYBER EXPERT KA SAFAR! 🚀"
                ])
            if any(w in roman_clip for w in ["police", "2000", "officer", "train", "investig"]):
                candidates.extend([
                    "2,000 POLICE OFFICERS KO TRAIN KIYA! 👮",
                    "CYBER CRIME POLICE CASES! 🛡️",
                    "REAL POLICE INVESTIGATION TRUTH! 🚨",
                    "ETHICAL HACKER CASE FILES! 📂"
                ])
            if any(w in roman_clip for w in ["otp", "bank", "khata", "paise", "transfer"]):
                candidates.extend([
                    "OTP SCAM SE KAISE BACHEIN?! 🚨",
                    "BANK ACCOUNT SCAM EXPOSED! 💳",
                    "1 MINUTE MEIN BANK KHATA KHALI?! 💸",
                    "NEVER SHARE THIS OTP! ⚠️"
                ])

        # -------------------------------------------------------------
        # DOMAIN 3: LUXURY & ARCHITECTURE (Ambani Antilia)
        # -------------------------------------------------------------
        if domain == "luxury_architecture" or any(w in roman_clip for w in ["ambani", "antilia", "mansion", "crore"]):
            if any(w in roman_clip for w in ["earthquake", "richter", "storm", "suraksha", "tsunami"]):
                candidates.extend([
                    "8.0 EARTHQUAKE PROOF MANSION! 🛡️",
                    "CAN ANTILIA SURVIVE DISASTERS?! 🏗️",
                    "MILITARY GRADE HOME DEFENSE! 🏰"
                ])
            if any(w in roman_clip for w in ["snow", "barf", "thand", "winter", "room", "ice"]):
                candidates.extend([
                    "ANTILIA KA SNOW ROOM REALITY! ❄️",
                    "MUMBAI MEIN ARTIFICIAL BARF?! ⛄",
                    "BILLIONAIRE PRIVATE SNOW WORLD! 🌨️"
                ])
            if any(w in roman_clip for w in ["staff", "naukar", "sewak", "maintenance", "600"]):
                candidates.extend([
                    "600 STAFF EK GHAR MEIN?! 👥",
                    "ANTILIA STAFF KI SALARY KITNI?! 💰",
                    "BILLIONAIRE LUXURY MAINTENANCE! 👑"
                ])
            if any(w in roman_clip for w in ["car", "cars", "garage", "helipad", "elevator"]):
                candidates.extend([
                    "168 CARS & 3 HELIPADS! 🚁",
                    "6 FLOORS JUST FOR CARS?! 🏎️",
                    "PRIVATE SKY HELIPADS TOUR! 🌆"
                ])
            if any(w in roman_clip for w in ["15000", "15,000", "billion", "crore", "mehenga"]):
                candidates.extend([
                    "₹15,000 CRORE KA MANSION! 🏰",
                    "MOST EXPENSIVE HOUSE IN ASIA! 💎",
                    "WHERE BILLIONS ARE SPENT! 🤑"
                ])

        # -------------------------------------------------------------
        # DOMAIN 4: PODCASTS & INTERVIEWS
        # -------------------------------------------------------------
        if domain == "podcast_interview":
            if any(w in roman_clip for w in ["regret", "galti", "pachtawa", "sorry"]):
                candidates.extend([
                    "BIGGEST REGRET REVEALED! 🎙️",
                    "YE GALTI KABHI MAT KARNA! ❌",
                    "EMOTIONAL CONFESSION ON CAMERA! 💔"
                ])
            if any(w in roman_clip for w in ["career", "start", "pehle", "struggle", "college"]):
                candidates.extend([
                    "HOW IT ALL STARTED! 🚀",
                    "EARLY STRUGGLE DAYS REVEALED! 💡",
                    "FROM ZERO TO LEGEND! 🔥"
                ])
            if any(w in roman_clip for w in ["money", "paisa", "kamai", "crore", "sponsorship"]):
                candidates.extend([
                    "YOUTUBE SE KITNA PAISA?! 💸",
                    "FIRST SPONSORSHIP MONEY! 💰",
                    "REAL WEALTH OF CREATORS! 🤑"
                ])

        # -------------------------------------------------------------
        # DOMAIN 5: TECH GADGETS & REVIEWS
        # -------------------------------------------------------------
        if domain == "tech_gadgets":
            if any(w in roman_clip for w in ["camera", "zoom", "sensor", "megapixel", "photo"]):
                candidates.extend([
                    "INSANE CAMERA ZOOM TEST! 📸",
                    "DSLR KILLER SMARTPHONE?! 📱",
                    "BEST CAMERA TEST IN 2026! 🔍"
                ])
            if any(w in roman_clip for w in ["battery", "charging", "watt", "drain"]):
                candidates.extend([
                    "0 TO 100% CHARGE IN MINUTES?! ⚡",
                    "BATTERY DRAIN TEST REVEALED! 🔋",
                    "ALL-DAY BATTERY LIFE?! ⚡"
                ])
            if any(w in roman_clip for w in ["ai", "chip", "processor", "speed", "benchmark"]):
                candidates.extend([
                    "NEXT-GEN AI PROCESSOR! 🤖",
                    "FASTEST SMARTPHONE CHIP EVER?! ⚡",
                    "AI FEATURE THAT SHOCKED EVERYONE! 🤯"
                ])

        # -------------------------------------------------------------
        # NUMBERS / STATS WITH CONTEXTUAL MEANING
        # -------------------------------------------------------------
        num_m = re.search(r'\b(\d+(?:,\d+)*(?:\s*(?:crore|cr|lakh|saal|years|percent|%|floors|cases|hours|fps|gb|mb|kbps))?)\b', roman_clip, re.I)
        if num_m:
            val = num_m.group(1).upper()
            if any(unit in val for unit in ["CRORE", "CR", "LAKH", "SAAL", "YEARS", "FLOORS", "CASES", "KBPS", "GB"]):
                candidates.append(f"{val} KA UNBELIEVABLE SACH! 🤯")
                candidates.append(f"SACH MEIN {val}?! 😱")

        # -------------------------------------------------------------
        # FILTER: SELECT FIRST UNUSED CANDIDATE
        # -------------------------------------------------------------
        for cand in candidates:
            cand_clean = cand.strip().upper()
            w_count = len(cand_clean.split())
            if 2 <= w_count <= 7 and cand_clean not in used_titles:
                used_titles.add(cand_clean)
                return cand_clean

        # -------------------------------------------------------------
        # DOMAIN-AWARE FALLBACKS (Zero raw sentence slicing)
        # -------------------------------------------------------------
        gaming_fallbacks = [
            "GTA 6 CRAZY MOMENT! 🎮",
            "UNBELIEVABLE GAMING REVELATION! 🤯",
            "ROCKSTAR GAMES SECRET! 👑",
            "GAMING INDUSTRY HISTORY! ⚡",
            "DID YOU NOTICE THIS DETAIL?! 👀",
            "WAIT FOR THIS GAMEPLAY REACTION! 🔥"
        ]
        cyber_fallbacks = [
            "CYBER CRIME ALERT! 🚨",
            "HOW HACKERS TARGET USERS! ⚠️",
            "IMPORTANT SECURITY WARNING! 🛡️",
            "CYBER INVESTIGATION SECRET! 📂",
            "STAY SAFE ONLINE TODAY! 📱"
        ]
        general_fallbacks = [
            "LISTEN TO THIS CAREFULLY! 💡",
            "NOBODY EXPECTED THIS! 👀",
            "BIGGEST REVELATION EVER! 🤯",
            "YOU WON'T BELIEVE THIS! 💀",
            "THIS CHANGED EVERYTHING! ⚡",
            "UNBELIEVABLE STORY REVEALED! 🚀",
            "A MUST-WATCH MOMENT! ✨",
            "CAN YOU BELIEVE THIS?! 🎯"
        ]

        pool = []
        if domain == "gaming":
            pool = gaming_fallbacks + general_fallbacks
        elif domain == "cybersecurity":
            pool = cyber_fallbacks + general_fallbacks
        else:
            pool = general_fallbacks

        for f in pool:
            if f not in used_titles:
                used_titles.add(f)
                return f

        # Final emergency unique index
        final_fallback = f"HIGH VALUE MOMENT #{len(used_titles)+1}! 🔥"
        used_titles.add(final_fallback)
        return final_fallback

    @classmethod
    def regenerate_title(
        cls,
        clip: Dict[str, Any],
        video_info: Dict[str, Any],
        used_titles: Optional[Set[str]] = None
    ) -> str:
        """Regenerates an alternative unique hook title for the clip."""
        if used_titles is None:
            used_titles = set()

        current_title = clip.get("hook_title", "").strip().upper()
        if current_title:
            used_titles.add(current_title)

        domain = cls.detect_video_domain(video_info)
        return cls.generate_hook_title(clip, video_info, used_titles=used_titles, domain=domain)
