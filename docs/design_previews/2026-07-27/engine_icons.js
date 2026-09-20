    const ENGINE_ICONS = {
        global: `<svg viewBox="0 0 32 32">
            <circle cx="16" cy="16" r="12" fill="none" stroke="var(--blue)" stroke-width="1.3"/>
            <g class="gl-rot">
                <ellipse cx="16" cy="16" rx="5.2" ry="12" fill="none" stroke="var(--blue)" stroke-width="1"/>
                <ellipse cx="16" cy="16" rx="9" ry="12" fill="none" stroke="var(--blue)" stroke-width="1" opacity=".55"/>
                <line x1="4" y1="16" x2="28" y2="16" stroke="var(--blue)" stroke-width=".8" opacity=".5"/>
            </g>
            <ellipse class="gl-orbit" cx="16" cy="16" rx="15" ry="4.5" fill="none" stroke="var(--blue-bright)" stroke-width="1" opacity=".5"/>
            <circle class="gl-wave" cx="22" cy="12" r="3" fill="none" stroke="var(--amber)" stroke-width="1"/>
            <circle class="gl-event" cx="22" cy="12" r="1.6" fill="var(--amber)"/>
        </svg>`,
        economy: `<svg viewBox="0 0 32 32">
            <path class="mk-trend" d="M4,20 L10,13 L15,17 L21,8 L28,12" fill="none" stroke="var(--slate-light)" stroke-width="1.1"/>
            <circle class="mk-marker" r="1.8" fill="var(--blue)"/>
            <circle cx="16" cy="16" r="2" fill="var(--blue)" opacity=".25"/>
            <g transform="translate(16,16)">
                <g class="mk-orbit-grp"><g transform="translate(0,-10)"><g class="mk-counter-grp">
                    <circle r="4.2" fill="#fff" stroke="var(--slate-100)" stroke-width=".6"/>
                    <text y="1.8" font-size="6" font-weight="800" fill="var(--blue)" text-anchor="middle">$</text>
                </g></g></g>
                <g class="mk-orbit-grp"><g transform="rotate(120) translate(0,-10)"><g class="mk-counter-grp">
                    <circle r="4.2" fill="#fff" stroke="var(--slate-100)" stroke-width=".6"/>
                    <text y="1.8" font-size="6" font-weight="800" fill="var(--blue)" text-anchor="middle">&#8364;</text>
                </g></g></g>
                <g class="mk-orbit-grp"><g transform="rotate(240) translate(0,-10)"><g class="mk-counter-grp">
                    <circle r="4.2" fill="#fff" stroke="var(--slate-100)" stroke-width=".6"/>
                    <text y="1.8" font-size="6" font-weight="800" fill="var(--blue)" text-anchor="middle">&#165;</text>
                </g></g></g>
            </g>
        </svg>`,
        ai: `<svg viewBox="0 0 32 32">
            <g stroke="var(--blue)" stroke-width="1" opacity=".55">
                <line class="ai-link" x1="16" y1="16" x2="7" y2="9"/>
                <line class="ai-link" x1="16" y1="16" x2="25" y2="9"/>
                <line class="ai-link" x1="16" y1="16" x2="7" y2="23"/>
                <line class="ai-link" x1="16" y1="16" x2="25" y2="23"/>
                <line class="ai-link" x1="16" y1="16" x2="16" y2="5"/>
            </g>
            <circle class="ai-node n1" cx="7" cy="9" r="2" fill="var(--blue)"/>
            <circle class="ai-node n2" cx="25" cy="9" r="2" fill="var(--blue)"/>
            <circle class="ai-node n3" cx="7" cy="23" r="2" fill="var(--blue)"/>
            <circle class="ai-node n4" cx="25" cy="23" r="2" fill="var(--blue)"/>
            <circle class="ai-node n5" cx="16" cy="5" r="2" fill="var(--blue)"/>
            <circle class="ai-core" cx="16" cy="16" r="3" fill="var(--blue)"/>
        </svg>`,
        gcc: `<svg viewBox="0 0 32 32">
            <rect x="4" y="16" width="5" height="12" fill="none" stroke="var(--slate-light)" stroke-width="1.1"/>
            <rect x="11" y="10" width="5" height="18" fill="none" stroke="var(--slate-light)" stroke-width="1.1"/>
            <rect x="18" y="14" width="5" height="14" fill="none" stroke="var(--slate-light)" stroke-width="1.1"/>
            <rect x="25" y="8" width="4" height="20" fill="none" stroke="var(--slate-light)" stroke-width="1.1"/>
            <g stroke="var(--blue)" stroke-width=".9" opacity=".6">
                <line class="gcc-link" x1="6.5" y1="16" x2="13.5" y2="10"/>
                <line class="gcc-link" x1="13.5" y1="10" x2="20.5" y2="14"/>
                <line class="gcc-link" x1="20.5" y1="14" x2="27" y2="8"/>
            </g>
            <circle class="gcc-packet" r="1.3" fill="var(--amber)" style="offset-path: path('M6.5,16 L13.5,10 L20.5,14 L27,8'); animation: ind-move 3.4s linear infinite;"/>
            <circle class="gcc-packet" r="1.3" fill="var(--amber)" style="offset-path: path('M27,8 L20.5,14 L13.5,10 L6.5,16'); animation: ind-move 3.4s linear infinite; animation-delay: 1.7s;"/>
            <circle class="gcc-node" cx="13.5" cy="10" r="3.4" fill="none" stroke="var(--blue-bright)" stroke-width="1" style="transform-origin:13.5px 10px;"/>
        </svg>`,
        insurance: `<svg viewBox="0 0 32 32">
            <path d="M16 4 L26 8 V16 C26 23 21.5 27.5 16 29 C10.5 27.5 6 23 6 16 V8 Z" fill="none" stroke="var(--slate-100)" stroke-width="1.4" pathLength="74"/>
            <path class="bf-shield-pulse" d="M16 4 L26 8 V16 C26 23 21.5 27.5 16 29 C10.5 27.5 6 23 6 16 V8 Z" fill="none" stroke="var(--blue-bright)" stroke-width="1.6" pathLength="74"/>
            <path class="bf-graph" d="M10 20 L13.5 17 L16.5 19 L21 13" fill="none" stroke="var(--blue)" stroke-width="1.3" stroke-linecap="round" pathLength="20"/>
            <g class="bf-lock">
                <rect x="14.3" y="18.5" width="4.4" height="3.6" rx=".6" fill="var(--navy)"/>
                <path d="M15.1 18.5 V17.2 a1.4 1.4 0 0 1 2.8 0 V18.5" fill="none" stroke="var(--navy)" stroke-width="1"/>
            </g>
        </svg>`,
        banking: `<svg viewBox="0 0 32 32">
            <line x1="6" y1="26" x2="26" y2="26" stroke="var(--blue)" stroke-width="1.3"/>
            <path d="M16 5 L26 11 H6 Z" fill="none" stroke="var(--blue)" stroke-width="1.3"/>
            <line class="bk-col c1" x1="9" y1="12" x2="9" y2="25" stroke="var(--blue)" stroke-width="1.1"/>
            <line class="bk-col c2" x1="14.3" y1="12" x2="14.3" y2="25" stroke="var(--blue)" stroke-width="1.1"/>
            <line class="bk-col c3" x1="17.7" y1="12" x2="17.7" y2="25" stroke="var(--blue)" stroke-width="1.1"/>
            <line class="bk-col c4" x1="23" y1="12" x2="23" y2="25" stroke="var(--blue)" stroke-width="1.1"/>
            <circle class="bk-coin" r="1.6" fill="var(--amber)" style="offset-path: path('M7,26 H25'); animation: ind-move 2.4s linear infinite;"/>
        </svg>`,
        manufacturing: `<svg viewBox="0 0 32 32">
            <path d="M4 25 L4 15 L11 15 L14 10 H22 L25 15 H28 V25 Z" fill="none" stroke="var(--slate-light)" stroke-width="1.2"/>
            <line x1="18" y1="10" x2="18" y2="5" stroke="var(--blue)" stroke-width="1.2"/>
            <g class="ind-arm"><line x1="12" y1="10" x2="12" y2="16" stroke="var(--blue)" stroke-width="1.4"/><circle cx="12" cy="16" r="1.4" fill="var(--blue)"/></g>
            <line class="ind-belt" x1="5" y1="25" x2="21" y2="25" stroke="var(--blue)" stroke-width="1.3"/>
            <rect width="2.6" height="2.6" fill="var(--amber)" style="offset-path: path('M5,25 H21'); animation: ind-move 2.2s linear infinite;"/>
            <g transform="translate(24,21)"><g class="ind-gear">
                <circle r="2.6" fill="none" stroke="var(--blue)" stroke-width="1"/>
                <circle r="0.9" fill="var(--blue)"/>
                <rect x="-0.7" y="-4" width="1.4" height="1.8" fill="var(--blue)"/>
                <rect x="-0.7" y="2.2" width="1.4" height="1.8" fill="var(--blue)"/>
                <rect x="-4" y="-0.7" width="1.8" height="1.4" fill="var(--blue)"/>
                <rect x="2.2" y="-0.7" width="1.8" height="1.4" fill="var(--blue)"/>
            </g></g>
        </svg>`,
        energy: `<svg viewBox="0 0 32 32">
            <circle cx="16" cy="15" r="10" fill="none" stroke="var(--slate-100)" stroke-width="1.4" pathLength="100"/>
            <circle class="en-ring-pulse" cx="16" cy="15" r="10" fill="none" stroke="var(--blue-bright)" stroke-width="1.6" pathLength="100"/>
            <path class="en-bolt" d="M17.5 6 L11 17 H15.5 L14 24 L21 12.5 H16.5 Z" fill="var(--amber)"/>
        </svg>`,
        defence: `<svg viewBox="0 0 32 32">
            <path d="M16 4 L25 8 V15 C25 22 21 26.5 16 28.5 C11 26.5 7 22 7 15 V8 Z" fill="none" stroke="var(--blue)" stroke-width="1.4"/>
            <g transform="translate(16,15)"><line class="def-sweep" x1="0" y1="0" x2="0" y2="-9" stroke="var(--blue-bright)" stroke-width="1.1" opacity=".8"/></g>
            <circle class="def-target" cx="16" cy="15" r="2.6" fill="none" stroke="var(--amber)" stroke-width="1" opacity="0"/>
            <path class="def-target" d="M16 11.4 V13 M16 17 V18.6 M12.4 15 H14 M18 15 H19.6" stroke="var(--amber)" stroke-width="1" opacity="0"/>
            <circle class="def-sat" r="1.1" fill="var(--slate)" style="offset-path: path('M4,15 A12,9 0 1 1 3.9,15'); animation: orbit-travel 6s linear infinite;"/>
        </svg>`,
        cyber: `<svg viewBox="0 0 32 32">
            <polygon class="cy-hex-pulse" points="16,4 26,10 26,22 16,28 6,22 6,10" fill="none" stroke="var(--blue)" stroke-width="1.4"/>
            <path d="M13 15.5 L15.3 18 L20 12" fill="none" stroke="var(--blue)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <rect class="cy-particle p1" x="10" y="22" width="1.6" height="1.6" fill="var(--blue-bright)"/>
            <rect class="cy-particle p2" x="15" y="23" width="1.6" height="1.6" fill="var(--blue-bright)"/>
            <rect class="cy-particle p3" x="20" y="22" width="1.6" height="1.6" fill="var(--blue-bright)"/>
            <rect class="cy-particle p4" x="17.5" y="24" width="1.6" height="1.6" fill="var(--blue-bright)"/>
        </svg>`,
        supplychain: `<svg viewBox="0 0 32 32">
            <path d="M3,24 Q9,24 9,18 Q9,12 16,12 Q23,12 23,20 Q23,26 29,26" fill="none" stroke="var(--slate-light)" stroke-width="1.1" stroke-dasharray="2 2.4"/>
            <rect x="1.5" y="21" width="3" height="3" fill="none" stroke="var(--slate)" stroke-width="1"/>
            <rect x="7" y="9" width="4" height="3.4" fill="none" stroke="var(--slate)" stroke-width="1"/>
            <path d="M20.5 17.5 H25.5 V22.5 H20.5 Z M20.5 17.5 L23 15 L25.5 17.5" fill="none" stroke="var(--slate)" stroke-width=".9"/>
            <rect x="27" y="23.5" width="3.4" height="3.4" fill="none" stroke="var(--slate)" stroke-width="1"/>
            <rect width="2.4" height="2.4" fill="var(--amber)" style="offset-path: path('M3,24 Q9,24 9,18 Q9,12 16,12 Q23,12 23,20 Q23,26 29,26'); animation: ind-move 5s linear infinite;"/>
        </svg>`,
        healthcare: `<svg viewBox="0 0 32 32">
            <path d="M16 6 V26 M6 16 H26" stroke="var(--blue)" stroke-width="2.6" stroke-linecap="round" opacity=".18"/>
            <path d="M2,16 H9 L11,10 L14,22 L16,16 H30" fill="none" stroke="var(--blue)" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            <circle r="1.6" fill="var(--amber)" style="offset-path: path('M2,16 H9 L11,10 L14,22 L16,16 H30'); animation: ind-move 2.6s linear infinite;"/>
            <g transform="translate(24,9)"><g class="hc-orbit">
                <circle cx="0" cy="-2.6" r="1" fill="var(--blue-bright)"/>
                <circle cx="0" cy="2.6" r="1" fill="var(--blue)"/>
            </g></g>
        </svg>`,
        telecom: `<svg viewBox="0 0 32 32">
            <path d="M16 28 L13 14 H19 Z" fill="none" stroke="var(--slate)" stroke-width="1.1"/>
            <line x1="16" y1="14" x2="16" y2="6" stroke="var(--slate)" stroke-width="1.1"/>
            <circle class="tc-ring r1" cx="16" cy="6" r="3" fill="none" stroke="var(--blue)" stroke-width="1" style="transform-origin:16px 6px;"/>
            <circle class="tc-ring r2" cx="16" cy="6" r="3" fill="none" stroke="var(--blue)" stroke-width="1" style="transform-origin:16px 6px;"/>
            <circle class="tc-ring r3" cx="16" cy="6" r="3" fill="none" stroke="var(--blue)" stroke-width="1" style="transform-origin:16px 6px;"/>
            <circle r="1.2" fill="var(--slate-light)" style="offset-path: path('M2,10 Q16,-4 30,10'); animation: orbit-travel 5s linear infinite;"/>
            <rect width="1.8" height="1.8" fill="var(--amber)" style="offset-path: path('M16,6 L16,26'); animation: ind-move 1.8s linear infinite;"/>
        </svg>`,
        climate: `<svg viewBox="0 0 32 32">
            <circle cx="16" cy="16" r="11" fill="none" stroke="var(--slate-100)" stroke-width="1.2"/>
            <path class="cl-leaf" d="M16 24 C10 22 9 15 14 9 C19 15 20 21 16 24 Z M16 24 V13" fill="none" stroke="var(--blue)" stroke-width="1.2"/>
            <path class="cl-wind" d="M3 12 H10 M4 16 H9" stroke="var(--slate-light)" stroke-width="1" stroke-linecap="round" stroke-dasharray="2 2"/>
            <circle class="cl-drop" cx="23" cy="9" r="1.3" fill="var(--blue-bright)"/>
            <path class="cl-sun" d="M25 22 A5 5 0 0 1 21 26" stroke="var(--amber)" stroke-width="1.2" fill="none" opacity="0"/>
            <circle class="cl-co2 a" cx="10" cy="25" r="1" fill="var(--slate-light)"/>
            <circle class="cl-co2 b" cx="21" cy="26" r="1" fill="var(--slate-light)"/>
        </svg>`
    };
    const ENGINE_ORDER = ['global','economy','ai','gcc','insurance','banking','manufacturing','energy','defence','cyber','supplychain','healthcare','telecom','climate'];
