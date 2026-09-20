/* Shared engine identity for all three previews.
   Emoji replaces the inline SVG icon set: the SVGs depended on keyframes
   defined in the live page's <style> block, so several rendered blank or
   static once extracted. Emoji render everywhere, for every engine, with
   no external dependency. */
const ENGINE_EMOJI = {
    global:        "🌍",  // globe
    economy:       "📈",  // chart increasing
    ai:            "🤖",  // robot
    gcc:           "🏢",  // office building
    insurance:     "🛡️",  // shield
    executive:     "👥",  // busts in silhouette
    banking:       "🏦",  // bank
    manufacturing: "🏭",  // factory
    energy:        "⚡",        // high voltage
    defence:       "🛰️",  // satellite
    cyber:         "🔒",  // lock
    supplychain:   "🚢",  // ship
    healthcare:    "🏥",  // hospital
    climate:       "🌱"   // seedling
};

const ENGINE_ORDER = ['global','economy','ai','gcc','insurance','banking',
    'manufacturing','energy','defence','cyber','supplychain','healthcare',
    'telecom','climate'];

/* telecom has no dedicated emoji above on purpose — it falls back below,
   so every engine id in ENGINE_ORDER always resolves to something visible. */
ENGINE_EMOJI.telecom = "📶";  // antenna bars

function emojiFor(id) { return ENGINE_EMOJI[id] || "●"; }
