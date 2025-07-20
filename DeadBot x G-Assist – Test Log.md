# DeadBot x G-Assist – Test Log 🐍🟢

---

## ⚡️ Contexte

**Testeur :** El Serda (aka DeadBot)  
**Build G-Assist :** Special 8Go VRAM / Hackathon NDA – 18/19 juillet 2025  
**Config Test :** RTX 3080, Ryzen 9 9950X3D, 31Go RAM, Win11 Pro  
**But :** Bench, flex, crowd-debug et comparer G-Assist pipeline avec DeadBot OSS (plugin “deadbot”, folder/module : snake_case, minuscule)

---

## 🚦 Fonctionnalités testées

- [x] Installation G-Assist patchée 8Go VRAM
- [x] Plugin detection (dossier “deadbot” reconnu après rename)
- [x] Diagnostic GPU/CPU/Telemetry OK (bench Cyberpunk, Guild Wars 1)
- [x] Support prompt multilingue (français/anglais)
- [x] GUI NVIDIA overlay : 20/20 (focus, transparence, UX)
- [x] Test sur crash/pipeline bottleneck (SSD, M2, réseau 5G en PLS…)

---

## 📝 Fun facts & Edge Cases

### 🟢 **Telemetry avant LLM**
- La télémétrie brute (GPU, CPU, VRAM…) est collectée côté driver/app AVANT toute analyse LLM.
- Le LLM reformule mais ne “voit” rien d’inédit :  
  → **Force crowd = plug n’importe quelle télémétrie dans DeadBot, et la synthèse sera tout aussi humaine !**

---

### 🟣 **SAFE_GUARD détecté**
- Tentative de commande non prévue (“deadbot !switch”) = refus instantané
- Réponse “I can assist with NVIDIA GPU and gaming optimizations in English.”
- **Impossible d’injecter/brancher un vrai plugin/fallback, SAFE_GUARD détecté côté G-Assist.**
- DeadBot = crowd modular, aucune guard, 100% user control.

---

### 🟠 **Comparatif diag : G-Assist vs DeadBot**
- G-Assist (en français) fait un résumé plus lisible qu’avant,  
  mais sans vrai verdict système (“surcharge”, “idle”, “Rien à signaler…”)
- DeadBot contextualise et explique la vraie santé du système
- **Ce qui manque côté G-Assist :**  
    - verdict humain,  
    - alerte simple,  
    - recommandation personnalisée,  
    - flexibilité OSS.

---

### 🟡 **Bottlenecks crowd IRL**
- Test SSD SATA vs M2 (upgrade Cyberpunk, 100% usage disque…)
- Test surcharge 5G (modem Poco overheat, désactivation auto 5G : crowd patience mode !)
- DeadBot détecte les goulots, G-Assist donne le “pavé” sans interprétation humaine.

---

### 🟤 **Langues & Prompt**
- G-Assist répond proprement en français (GG), mais repasse en anglais si SAFE_GUARD triggered.
- DeadBot crowd-support tout prompt/langue/context.

---

### 🟤 **Modularité plugin**
- Renommer le dossier (“Plugin-Nvidia” → “deadbot”) = fonctionne direct : pipeline crowd-ready, pas de hardcode/bug sur le nom.

---

## 🧪 Prochaines idées/tests

- Fallback LLM (Ollama, openai, local gguf…) dans le pipeline plugin
- Overlay crowd custom, lecture des crashs, gestion des “features crowd”
- Proposer un menu crowd DeadBot directement dans l’overlay G-Assist (si possible)

---

## 📝 Résumé à la team dev

- G-Assist 8Go fonctionne, diag GPU OK, GUI top niveau
- MAIS SAFE_GUARD bloque tout plugin/fallback/user control (DeadBot style impossible)
- Reco crowd : **ouvrir l’API/plugin/LLM fallback, laisser la communauté crowd-hacker, crowd-debug, crowd-inventer**
- **DeadBot crowd a toujours un coup d’avance sur la lisibilité, la contextualisation, et le fun !**

---

> **OSS crowd note:**  
> “Bravo pour la réactivité, mais la crowd veut encore plus de flex et de contrôle !  
>  
> DeadBot n’est pas mort… il s’adapte !”

---

*Logguer tout ça, et vive la prochaine vague OSS/hackathon !*
