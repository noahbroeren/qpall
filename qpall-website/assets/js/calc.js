/* Q-Pall laadcalculator */
(function () {
if (!document.getElementById('qpc')) return;
/* Q-Pall laadcalculator: rekenmotor + palletgegevens.
   Letterlijk overgenomen uit calculator-embed.html (Noah, oktober 2026; regels 82-1500, zonder de ingesloten foto's).
   Aanpassingen: 27-10-2026 (Q-Pall) 0,1 m marge ook in de hoogte (MARGIN_H); 9-11-2026 (update 38) vaste stapels
   (displaypallets, folie) die te hoog zijn voor de laadruimte (20 ft / 40 ft container) worden lager gestapeld, in hele
   lagen (perLayer), in plaats van "past niet".
   Pallets met klikbare onderlatten (QP…LB3RR, Q-Pall 9-11-2026) zijn nestbaar: genest geleverd, 3 onderlatten per
   pallet los op aparte onderlatpallets (CLICK_RUNNER, defaultRunners).
   EUROPAL800RR en RECYCPAL1210RR (Q-Pall via Noah, 10-11-2026): om en om gestapeld (ondersteboven in elkaar), 23 per
   stapel, stapel 2050 mm hoog, op een plaats van 1200 x 1000 / 1200 x 1200: vaste stapel (palletH, useFixedLimit), dus
   ook in een container 23 per plaats.
   QP4048MB3RR (1220 x 1020) eruit (update 45, Noah 10-11-2026: de 48 x 40-pallets staan niet meer op de site).
   Verder niet aanpassen: de weergave staat in ui.js. build_assets.py plakt beide samen tot /assets/js/calc.js. */
        // Trailer Specifications (Lengths in mm, Width 2450mm, Heights vary)
        const trailers = {
            tautliner: { name: "Standard Tautliner", lengths: [13600], width: 2450, height: 2650 },
            mega: { name: "Mega Trailer", lengths: [13600], width: 2450, height: 3000 },
            combi77: { name: "Combi 7.7x7.7", lengths: [7700, 7700], width: 2450, height: 3000 },
            combi78: { name: "Combi 7x8", lengths: [7000, 8000], width: 2450, height: 3000 },
            container20: { name: "Container – 20FT", lengths: [5850], width: 2310, height: 2250 },
            container20hc: { name: "Container – 20FT high cube", lengths: [5850], width: 2310, height: 2580 },
            container40: { name: "Container – 40FT", lengths: [11950], width: 2310, height: 2250 },
            container40hc: { name: "Container – 40FT high cube", lengths: [11950], width: 2310, height: 2580 },
            container45: { name: "Container – 45FT", lengths: [13500], width: 2310, height: 2520 },
            container45hc: { name: "Container – 45FT high cube", lengths: [13550], width: 2340, height: 2580 },
            container45pw: { name: "Container – 45FT palletwide", lengths: [13500], width: 2410, height: 2520 }
        };

        // Runner pallets
        const runnerPallets = {
            "QP-RUN-L": { id: "QP-RUN-L", name: "QP-RUNL", l: 1200, w: 1000, h: 800, perPallet: 270, limitTautliner: 3, limitCombi: 3 },
            "QP-RUN-H": { id: "QP-RUN-H", name: "QP-RUNH", l: 1200, w: 1000, h: 800, perPallet: 150, limitTautliner: 3, limitCombi: 3 },
            "QPRUN1111L": { id: "QPRUN1111L", name: "QPRUN1111L", l: 1200, w: 800, h: 800, perPallet: 180, limitTautliner: 3, limitCombi: 3 },
            "QPRUN1140L": { id: "QPRUN1140L", name: "QPRUN1140L", l: 1200, w: 800, h: 800, perPallet: 180, limitTautliner: 3, limitCombi: 3 },
            "QPRUN1212L": { id: "QPRUN1212L", name: "QPRUN1212L", l: 1200, w: 800, h: 800, perPallet: 180, limitTautliner: 3, limitCombi: 3 }
        };
        const defaultRunners = {
            "QP1111LB9FR": "QPRUN1111L",
            "QP1140LB9FR": "QPRUN1140L",
            "QP1212LB9FR": "QPRUN1212L",
            // light pallets with 3 click-on runners (update 38, Q-Pall): delivered nested, 3 runners per pallet loose
            // on separate runner pallets
            "QP76114LB3RR": "QP-RUN-L",
            "QP1208LB3RR": "QP-RUN-L",
            "QP1210LB3RR": "QP-RUN-L",
            "QP1111LB3RR": "QPRUN1111L",
            "QP1140LB3RR": "QPRUN1140L",
            "QP1212LB3RR": "QPRUN1212L"
        };
        // the light 3-runner pallets above: nestable like the 9-feet pallet, the runners travel separately
        const CLICK_RUNNER = new Set(["QP76114LB3RR", "QP1208LB3RR", "QP1210LB3RR", "QP1111LB3RR", "QP1140LB3RR", "QP1212LB3RR"]);

        // Pallet Database extracted from user's PDF list
        const pallets = [
            { id: "QP6040MB4F", name: "QP6040MB4F (600x400)", l: 1200, w: 1000, h: 150, palletH: 2200, limitTautliner: 200, limitCombi: 200, unitL: 600, unitW: 400, unitH: 155, perLayer: 4 },
            { id: "QP6040HB4F", name: "QP6040HB4F (600x400)", l: 1200, w: 1000, h: 150, palletH: 2200, limitTautliner: 200, limitCombi: 200, unitL: 600, unitW: 400, unitH: 155, perLayer: 4 },
            { id: "QP6080LR3RR", name: "QP6080LR3RR (600x800)", l: 1200, w: 800, h: 145, palletH: 2320, limitTautliner: 100, limitCombi: 100, useFixedLimit: true, perLayer: 2 },
            { id: "QP6080M6FR", name: "QP6080M6FR (600x800)", l: 1200, w: 800, h: 145, palletH: 2200, limitTautliner: 80, limitCombi: 80, useFixedLimit: true, perLayer: 2 },
            { id: "QP6080HB6FR", name: "QP6080HB6FR (600x800)", l: 1200, w: 800, h: 155, palletH: 2200, limitTautliner: 80, limitCombi: 80, useFixedLimit: true, perLayer: 2 },
            { id: "QP76114LB9FR", name: "QP76114LB9FR (760x1140)", l: 760, w: 1140, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 50 },
            { id: "QP76114LB3RR", name: "QP76114LB3RR (760x1140)", l: 760, w: 1140, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 50, clickRunner: true },
            { id: "QP1111LB9FR", name: "QP1111LB9FR (1100x1100)", l: 1100, w: 1100, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 45 },
            { id: "QP1111LB3RR", name: "QP1111LB3RR (1100x1100)", l: 1100, w: 1100, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 45, clickRunner: true },
            { id: "QP1111MB3R-AS", name: "QP1111MB3R-AS (1100x1100)", l: 1100, w: 1100, h: 150, limitTautliner: 17, limitCombi: 19 },
            { id: "QP1111HB3RR", name: "QP1111HB3RR (1100x1100)", l: 1100, w: 1100, h: 165, limitTautliner: 15, limitCombi: 17 },
            { id: "QP1140LB9FR", name: "QP1140LB9FR (1140x1140)", l: 1140, w: 1140, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 45 },
            { id: "QP1140LB3RR", name: "QP1140LB3RR (1140x1140)", l: 1140, w: 1140, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 45, clickRunner: true },
            { id: "QP1140MB3RR", name: "QP1140MB3RR (1140x1140)", l: 1140, w: 1140, h: 156, limitTautliner: 16, limitCombi: 18 },
            { id: "QP1140HB3RR", name: "QP1140HB3RR (1140x1140)", l: 1140, w: 1140, h: 165, limitTautliner: 15, limitCombi: 17 },
            { id: "QP1140MB3R-PAS", name: "QP1140MB3R-PAS (1140x1140)", l: 1140, w: 1140, h: 150, limitTautliner: 17, limitCombi: 19 },
            { id: "QP1208LB9FR", name: "QP1208LB9FR (1200x800)", l: 1200, w: 800, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 50 },
            { id: "QP1208LB9FR-FOLIE", name: "QP1208LB9FR folie (1200x800)", l: 1200, w: 800, h: 150, palletH: 2130, limitTautliner: 40, limitCombi: 40, useFixedLimit: true },
            { id: "QP1208LB3RR", name: "QP1208LB3RR (1200x800)", l: 1200, w: 800, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 50, clickRunner: true },
            { id: "QP1208MB3RR", name: "QP1208MB3RR (1200x800)", l: 1200, w: 800, h: 145, limitTautliner: 17, limitCombi: 19 },
            { id: "QP1208HB3RR", name: "QP1208HB3RR (1200x800)", l: 1200, w: 800, h: 159, limitTautliner: 15, limitCombi: 18 },
            { id: "EUROPAL800RR", name: "EUROPAL800RR (1200x800)", l: 1200, w: 1000, h: 150, palletH: 2050, limitTautliner: 23, limitCombi: 23, useFixedLimit: true },
            { id: "QP1210LB9FR", name: "QP1210LB9FR (1200x1000)", l: 1200, w: 1000, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 50 },
            { id: "QP1210LB9FR-FOLIE", name: "QP1210LB9FR folie (1200x1000)", l: 1200, w: 1000, h: 150, palletH: 2130, limitTautliner: 40, limitCombi: 40, useFixedLimit: true },
            { id: "QP1210LB3RR", name: "QP1210LB3RR (1200x1000)", l: 1200, w: 1000, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 50, clickRunner: true },
            { id: "QP1210MB3RR", name: "QP1210MB3RR (1200x1000)", l: 1200, w: 1000, h: 150, limitTautliner: 17, limitCombi: 19 },
            { id: "QP1210HB3RR", name: "QP1210HB3RR (1200x1000)", l: 1200, w: 1000, h: 160, limitTautliner: 15, limitCombi: 18 },
            { id: "QP1210HP3R-AO", name: "QP1210HP3R-AO (1200x1000)", l: 1200, w: 1000, h: 165, limitTautliner: 15, limitCombi: 17 },
            { id: "RECYCPAL1210RR", name: "RECYCPAL1210RR (1200x1000)", l: 1200, w: 1200, h: 150, palletH: 2050, limitTautliner: 23, limitCombi: 23, useFixedLimit: true },
            { id: "QP1212LB9FR", name: "QP1212LB9FR (1200x1200)", l: 1200, w: 1200, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 45 },
            { id: "QP1212LB3RR", name: "QP1212LB3RR (1200x1200)", l: 1200, w: 1200, h: 150, limitTautliner: 45, limitCombi: 55, nestPitch: 45, clickRunner: true },
            { id: "QP1212MB3RR", name: "QP1212MB3RR (1200x1200)", l: 1200, w: 1200, h: 156, limitTautliner: 16, limitCombi: 18 },
            { id: "QP1212HB3RR", name: "QP1212HB3RR (1200x1200)", l: 1200, w: 1200, h: 165, limitTautliner: 15, limitCombi: 17 },
            { id: "QP1311MB3R-AS", name: "QP1311MB3R-AS (1300x1100)", l: 1300, w: 1100, h: 150, limitTautliner: 17, limitCombi: 19 },
            { id: "QP1311HB3R-AS", name: "QP1311HB3R-AS (1300x1100)", l: 1300, w: 1100, h: 158, limitTautliner: 15, limitCombi: 18 },
            { id: "QP1311HB3R", name: "QP1311HB3R (1300x1100)", l: 1300, w: 1100, h: 160, limitTautliner: 15, limitCombi: 18 },
            // Runners als standalone product
            { id: "QP-RUN-L-standalone", name: "QP-RUNL (runners — 270/pallet)", l: 1200, w: 1000, h: 800, limitTautliner: 3, limitCombi: 3, isRunner: true, perPallet: 270 },
            { id: "QP-RUN-H-standalone", name: "QP-RUNH (runners — 150/pallet)", l: 1200, w: 1000, h: 800, limitTautliner: 3, limitCombi: 3, isRunner: true, perPallet: 150 },
            { id: "QPRUN1111L-standalone", name: "QPRUN1111L (runners — 180/pallet)", l: 1200, w: 800, h: 800, limitTautliner: 3, limitCombi: 3, isRunner: true, perPallet: 180 },
            { id: "QPRUN1140L-standalone", name: "QPRUN1140L (runners — 180/pallet)", l: 1200, w: 800, h: 800, limitTautliner: 3, limitCombi: 3, isRunner: true, perPallet: 180 },
            { id: "QPRUN1212L-standalone", name: "QPRUN1212L (runners — 180/pallet)", l: 1200, w: 800, h: 800, limitTautliner: 3, limitCombi: 3, isRunner: true, perPallet: 180 }
        ];

let lastResult = null;
const SKUIMG={"QP6040MB4F": "display-pallet-600-x-400-x-155-open-deck-4-feet-medium", "QP6040HB4F": "display-pallet-600-x-400-x-155-open-deck-4-feet-medium", "QP6080LR3RR": "display-pallet-800-x-600-x-145-open-deck-3-runners-light", "QP6080M6FR": "display-pallet-800-x-600-x-143-open-deck-6-feet-medium", "QP6080HB6FR": "display-pallet-800-x-600-x-155-open-deck-6-feet-heavy", "QP76114LB9FR": "plastic-pallet-1140-x-760-x-150-open-deck-9-feet-light", "QP76114LB3RR": "plastic-pallet-760-x-1140-x-158-open-deck-3-runners-light", "QP1111LB9FR": "plastic-pallet-1100-x-1100-x-150-open-deck-9-feet-light", "QP1111LB3RR": "plastic-pallet-1100-x-1100-x-158-open-deck-3-runners-light", "QP1111MB3R-AS": "plastic-pallet-1100-x-1100-x-150-open-deck-3-runners-medium", "QP1111HB3RR": "plastic-pallet-1100-x-1100-x-165-open-deck-3-runners-heavy", "QP1140LB9FR": "plastic-pallet-1140-x-1140-x-150-open-deck-9-feet-light", "QP1140LB3RR": "plastic-pallet-1140-x-1140-x-158-open-deck-3-runners-light", "QP1140MB3RR": "plastic-pallet-1140-x-1140-x-156-open-deck-3-runners-medium", "QP1140HB3RR": "plastic-pallet-1140-x-1140-x-165-open-deck-3-runners-heavy", "QP1140MB3R-PAS": "plastic-pallet-1140-x-1140-x-150-open-deck-3-runners-medium", "QP1208LB9FR": "plastic-pallet-1200-x-800-x-150-open-deck-9-feet-light", "QP1208LB9FR-FOLIE": "plastic-pallet-1200-x-800-x-150-open-deck-9-feet-light", "QP1208LB3RR": "plastic-pallet-1200-x-800-x-160-open-deck-3-runners-light", "QP1208MB3RR": "plastic-pallet-1200-x-800-x-145-open-deck-3-runners-medium", "QP1208HB3RR": "plastic-pallet-1200-x-800-x-159-open-deck-3-runners-heavy", "EUROPAL800RR": "h1-euro-pallet-1200-x-800-x-160-open-deck-3-runners-heavy", "QP1210LB9FR": "plastic-pallet-1200-x-1000-x-150-open-deck-9-feet-light", "QP1210LB9FR-FOLIE": "plastic-pallet-1200-x-1000-x-150-open-deck-9-feet-light", "QP1210LB3RR": "plastic-pallet-1200-x-1000-x-150-open-deck-3-runners-light", "QP1210MB3RR": "plastic-pallet-1200-x-1000-x-150-open-deck-3-runners-medium", "QP1210HB3RR": "plastic-pallet-1200-x-1000-x-160-open-deck-3-runners-heavy", "QP1210HP3R-AO": "plastic-pool-pallet-1200-x-1000-x-165-open-anti-slip-deck-3-runners-heavy", "RECYCPAL1210RR": "industrial-pallet-1200-x-1000-x-160-open-deck-3-runners-heavy", "QP1212LB9FR": "plastic-pallet-1200-x-1200-x-150-open-deck-9-feet-light", "QP1212LB3RR": "plastic-pallet-1200-x-1200-x-158-open-deck-3-runners-light", "QP1212MB3RR": "plastic-pallet-1200-x-1200-x-156-open-deck-3-runners-medium", "QP1212HB3RR": "plastic-pallet-1200-x-1200-x-165-open-deck-3-runners-heavy", "QP1311MB3R-AS": "plastic-pallet-1300-x-1100-x-158-open-deck-3-runners-heavy", "QP1311HB3R-AS": "plastic-pallet-1300-x-1100-x-158-open-deck-3-runners-heavy", "QP1311HB3R": "plastic-pallet-1300-x-1100-x-160-open-deck-3-runners-heavy"};
        function addPalletRow() {
            const container = document.getElementById('palletRowsContainer');
            const rowId = (window.__qpRid = (window.__qpRid||0) + 1);

            const row = document.createElement('div');
            row.className = 'pallet-row';
            row.id = `row-${rowId}`;

            let optionsHtml = '';
            pallets.forEach(p => {
                optionsHtml += `<option value="${p.name}"></option>`;
            });

            row.innerHTML = `
        <div class="form-group" style="flex: 2;">
            <label>Select Pallet</label>
            <input list="pallets-list-${rowId}" class="pallet-select" placeholder="Search or select pallet...">
            <datalist id="pallets-list-${rowId}">
                ${optionsHtml}
            </datalist>
        </div>
        <div class="form-group" style="flex: 1;">
            <label>Quantity</label>
            <input type="text" class="pallet-amount" placeholder="Quantity or 'fill'" value="fill">
        </div>
        <button class="remove-btn" onclick="removePalletRow('row-${rowId}')">✕</button>
    `;

            container.appendChild(row);

            // Listen for changes in the pallet selection
            const input = row.querySelector('.pallet-select');
            if (input) {
                input.addEventListener('input', checkRunnersVisibility);
            }

            updateMixStrategyVisibility();
            checkRunnersVisibility();
        }

        function checkRunnersVisibility() {
            const specialPallets = ['QP76114LB9FR', 'QP1208LB9FR', 'QP1210LB9FR', 'QP1111LB9FR', 'QP1140LB9FR', 'QP1212LB9FR'];
            const inputs = document.querySelectorAll('.pallet-select');
            let specialSelected = [];

            inputs.forEach((input, index) => {
                const val = input.value;
                if (specialPallets.some(sp => val.includes(sp))) {
                    let displayName = val.split('(')[0].trim();
                    if (!displayName) displayName = val;
                    specialSelected.push({ val: displayName, index: index });
                }
            });

            const runnersSection = document.getElementById('runnersSection');
            const dynamicContainer = document.getElementById('dynamicRunnerSelections');

            if (runnersSection && dynamicContainer) {
                if (specialSelected.length > 0) {
                    runnersSection.style.display = 'block';

                    const existingMap = new Map();
                    dynamicContainer.querySelectorAll('.dynamic-runner-select').forEach(sel => {
                        existingMap.set(sel.id, sel.value);
                    });

                    let htmlContent = '';
                    specialSelected.forEach(item => {
                        const selectId = `runnerSelect_${item.index}`;
                        const currentVal = existingMap.has(selectId) ? existingMap.get(selectId) : "";
                        const attr0 = currentVal === "" || !currentVal ? "selected" : "";

                        let optionsHtml = `<option value="" disabled ${attr0}>Choose a runner type...</option>`;
                        optionsHtml += `<option value="none" ${currentVal === "none" ? "selected" : ""}>No runner</option>`;
                        if (typeof runnerPallets !== "undefined") {
                            let allowedRunners = [];
                            if (['QP76114LB9FR', 'QP1208LB9FR', 'QP1210LB9FR', 'QP1208LB9FR folie', 'QP1210LB9FR folie'].includes(item.val)) {
                                allowedRunners = ['QP-RUN-L', 'QP-RUN-H'];
                            } else if (typeof defaultRunners !== "undefined" && defaultRunners[item.val]) {
                                allowedRunners = [defaultRunners[item.val]];
                            } else {
                                // Fallback just in case, show all
                                allowedRunners = Object.keys(runnerPallets);
                            }

                            allowedRunners.forEach(rId => {
                                if (runnerPallets[rId]) {
                                    let r = runnerPallets[rId];
                                    optionsHtml += `<option value="${r.id}" ${currentVal === r.id ? "selected" : ""}>${r.name}</option>`;
                                }
                            });
                        }

                        htmlContent += `
                            <div class="form-group runner-group">
                                <label for="${selectId}">Runner Type for ${item.val}</label>
                                <select id="${selectId}" class="dynamic-runner-select" required>
                                    ${optionsHtml}
                                </select>
                            </div>
                        `;
                    });
                    dynamicContainer.innerHTML = htmlContent;
                } else {
                    runnersSection.style.display = 'none';
                    dynamicContainer.innerHTML = '';
                }
            }
        }

        function removePalletRow(rowId) {
            const row = document.getElementById(rowId);
            if (row) {
                row.remove();
                updateMixStrategyVisibility();
                checkRunnersVisibility();
            }
        }

        function updateMixStrategyVisibility() {
            const palletRows = document.querySelectorAll('.pallet-row');
            const mixStrategySection = document.querySelector('.qpc-config');
            if (mixStrategySection) {
                if (palletRows.length >= 2) {
                    mixStrategySection.style.display = 'block';
                } else {
                    mixStrategySection.style.display = 'none';
                }
            }
        }

        // Logic to calculate floor spaces for a given pallet and floor area
        function getOptimalFloorSpaces(pallet, floorLength, floorWidth) {
            const l1 = Math.floor(floorLength / pallet.l);
            const w1 = Math.floor(floorWidth / pallet.w);
            const spaces1 = l1 * w1;

            const l2 = Math.floor(floorLength / pallet.w);
            const w2 = Math.floor(floorWidth / pallet.l);
            const spaces2 = l2 * w2;

            return Math.max(spaces1, spaces2);
        }

        function calculateSegmentSpaces(pallet, segmentLength, floorWidth) {
            let bestSpaces = 0;
            let bestLengthConsumed = 0;

            const cols1 = Math.floor(floorWidth / pallet.w);
            const maxRows1 = Math.floor(segmentLength / pallet.l);

            const cols2 = Math.floor(floorWidth / pallet.l);
            const maxRows2 = Math.floor(segmentLength / pallet.w);

            // Try starting with Lengthwise rows, filling the rest with Widthwise rows
            for (let rows1 = 0; rows1 <= maxRows1; rows1++) {
                const length1 = rows1 * pallet.l;
                const remainder = segmentLength - length1;
                const rows2 = Math.floor(remainder / pallet.w);
                const length2 = rows2 * pallet.w;

                const spaces = (rows1 * cols1) + (rows2 * cols2);
                const lengthConsumed = length1 + length2;

                if (spaces > bestSpaces || (spaces === bestSpaces && lengthConsumed < bestLengthConsumed)) {
                    bestSpaces = spaces;
                    bestLengthConsumed = lengthConsumed;
                }
            }

            // Try starting with Widthwise rows, filling the rest with Lengthwise rows
            for (let rows2 = 0; rows2 <= maxRows2; rows2++) {
                const length2 = rows2 * pallet.w;
                const remainder = segmentLength - length2;
                const rows1 = Math.floor(remainder / pallet.l);
                const length1 = rows1 * pallet.l;

                const spaces = (rows1 * cols1) + (rows2 * cols2);
                const lengthConsumed = length1 + length2;

                if (spaces > bestSpaces || (spaces === bestSpaces && lengthConsumed < bestLengthConsumed)) {
                    bestSpaces = spaces;
                    bestLengthConsumed = lengthConsumed;
                }
            }

            return { spaces: bestSpaces, lengthConsumed: bestLengthConsumed, widthConsumed: 0 };
        }

        function getMinimumLengthForSpaces(pallet, requiredSpaces, floorWidth, maxSegmentLength) {
            let bestLength = Infinity;

            const cols1 = Math.floor(floorWidth / pallet.w);
            const maxRows1 = Math.floor(maxSegmentLength / pallet.l);

            const cols2 = Math.floor(floorWidth / pallet.l);
            const maxRows2 = Math.floor(maxSegmentLength / pallet.w);

            for (let rows1 = 0; rows1 <= maxRows1; rows1++) {
                const length1 = rows1 * pallet.l;
                let spaces1 = rows1 * cols1;
                if (spaces1 >= requiredSpaces) {
                    bestLength = Math.min(bestLength, length1);
                    continue;
                }

                let neededFrom2 = requiredSpaces - spaces1;
                if (cols2 > 0) {
                    let rows2 = Math.ceil(neededFrom2 / cols2);
                    let length2 = rows2 * pallet.w;
                    let totalLength = length1 + length2;
                    if (totalLength <= maxSegmentLength) {
                        bestLength = Math.min(bestLength, totalLength);
                    }
                }
            }

            for (let rows2 = 0; rows2 <= maxRows2; rows2++) {
                const length2 = rows2 * pallet.w;
                let spaces2 = rows2 * cols2;
                if (spaces2 >= requiredSpaces) {
                    bestLength = Math.min(bestLength, length2);
                    continue;
                }

                let neededFrom1 = requiredSpaces - spaces2;
                if (cols1 > 0) {
                    let rows1 = Math.ceil(neededFrom1 / cols1);
                    let length1 = rows1 * pallet.l;
                    let totalLength = length1 + length2;
                    if (totalLength <= maxSegmentLength) {
                        bestLength = Math.min(bestLength, totalLength);
                    }
                }
            }

            return bestLength === Infinity ? null : bestLength;
        }

        // Helper: LB + digit(s) + F in name = nestable (150mm base + nestPitch per extra pallet)
        // QP6040 explicitly excluded (fixed limit), QP6080xF are NOT nestable (fixed on pallet)
        function isNestableLBF(id) {
            return (/LB\d+F/.test(id) && !id.startsWith('QP6040')) || CLICK_RUNNER.has(id);
        }
        // Margin of 0.1 m (Q-Pall, 27-10-2026): kept free in the length of every loading space (see 'marge' below)
        // and in the height (stack heights are calculated against height - MARGIN_H). Not in the width: three
        // euro pallets side by side (2400 mm) must still fit a 2450 mm trailer.
        const MARGIN_H = 100;
        // Helper: never allowed on side in containers — same set as nestable
        function isNeverOnSide(id) {
            return /LB\d+F/.test(id) || CLICK_RUNNER.has(id);
        }
        // Helper: get stackCount for a nestable pallet in a container of height cH
        // Uses pallet.nestPitch if defined, else 50mm default
        function getNestStackCount(palletObj, cH) {
            let pitch = (palletObj && palletObj.nestPitch) ? palletObj.nestPitch : 50;
            return Math.floor((cH - 150) / pitch) + 1;
        }
        function calculateLoad() {
            const runnersSection = document.getElementById('runnersSection');
            if (runnersSection && runnersSection.style.display !== 'none') {
                const runnerSelects = document.querySelectorAll('.dynamic-runner-select');
                for (let i = 0; i < runnerSelects.length; i++) {
                    if (!runnerSelects[i].value) {
                        alert((window.QPC_T && window.QPC_T.err_runner) || "Please select a runner type for each selected nestable pallet.");
                        return;
                    }
                }
            }

            const trailerId = document.getElementById('trailerSelect').value;
            const strategy = document.getElementById('strategySelect') ? document.getElementById('strategySelect').value : "fair_split";
            const trailer = trailers[trailerId];

            // Get percentage of trailer available
            const percentageStr = document.getElementById('trailerPercentage').value;
            let availablePercentage = parseFloat(percentageStr);
            if (isNaN(availablePercentage) || availablePercentage < 0) availablePercentage = 100;
            if (availablePercentage > 100) availablePercentage = 100;
            availablePercentage = availablePercentage / 100;

            const palletRows = document.querySelectorAll('.pallet-row');
            if (palletRows.length === 0) {
                alert((window.QPC_T && window.QPC_T.err_none) || "Please add at least one pallet type.");
                return;
            }

            // Gather selected pallets and their amounts
            let loadItems = [];
            Array.from(palletRows).forEach((row, index) => {
                const select = row.querySelector('.pallet-select');
                const amountInput = row.querySelector('.pallet-amount');
                if (!select || !amountInput) return;

                const val = select.value;
                const amountStr = amountInput.value.trim().toLowerCase();

                let amount = 'fill';
                if (amountStr !== 'fill' && amountStr !== '') {
                    const parsed = parseInt(amountStr, 10);
                    if (!isNaN(parsed) && parsed > 0) {
                        amount = parsed;
                    }
                }

                let found = pallets.find(p => p.id === val || p.name === val);
                // Fixed stacks (display pallets, foil-wrapped stacks) that are higher than the loading space, such as
                // 2200 mm in a 20 ft container (2150 mm usable): load a lower stack instead of nothing (update 38, Noah).
                // Whole layers only (perLayer pallets per layer); the stack height shrinks in proportion.
                if (found && found.palletH && (found.id.startsWith('QP6040') || found.useFixedLimit)) {
                    const usableH = trailer.height - MARGIN_H;
                    if (found.palletH > usableH) {
                        const per = found.perLayer || 1, layers = Math.floor(found.limitTautliner / per);
                        const fit = Math.floor(layers * usableH / found.palletH);
                        if (fit >= 1) {
                            found = Object.assign({}, found, { palletH: Math.floor(found.palletH * fit / layers),
                                limitTautliner: fit * per, limitCombi: Math.min(found.limitCombi, fit * per) });
                        }
                    }
                }
                if (found) {
                    let stackFactor;
                    if (found.isRunner) {
                        // Standalone runners: stackFactor = pallets hoog × runners per pallet
                        const isCombiOrMega = trailerId === 'combi77' || trailerId === 'combi78' || trailerId === 'mega';
                        const stackHigh = isCombiOrMega ? found.limitCombi : found.limitTautliner;
                        stackFactor = stackHigh * found.perPallet;
                    } else if (found.isCustom) {
                        let maxHeight = trailer.height - MARGIN_H;
                        if (found.isNestable) {
                            stackFactor = 1 + Math.floor((maxHeight - found.h) / found.nestHeight);
                        } else {
                            stackFactor = Math.floor(maxHeight / found.h);
                        }
                        if (stackFactor < 1) stackFactor = 1;
                    } else if (trailerId.startsWith('container')) {
                        // QP6040: fixed limit (200 units per pallet position)
                        if (found.id.startsWith('QP6040')) {
                            stackFactor = found.limitTautliner;
                        // Pallets with fixed stack limit (e.g. 6080): use limitTautliner like trailers
                        } else if (found.useFixedLimit) {
                            stackFactor = found.limitTautliner;
                        // Nestable LBxF: dynamic nest pitch from pallet data
                        } else if (isNestableLBF(found.id)) {
                            stackFactor = getNestStackCount(found, trailer.height - MARGIN_H);
                        } else {
                            stackFactor = Math.floor((trailer.height - MARGIN_H) / found.h);
                        }
                        if (stackFactor < 1) stackFactor = 1;
                    } else {
                        const isCombiOrMega = trailerId === 'combi77' || trailerId === 'combi78' || trailerId === 'mega';
                        stackFactor = isCombiOrMega ? found.limitCombi : found.limitTautliner;
                    }

                    let cleanVal = val.split('(')[0].trim();
                    let rType = null;
                    const specialPalletsList = ['QP76114LB9FR', 'QP1208LB9FR', 'QP1210LB9FR', 'QP1111LB9FR', 'QP1140LB9FR', 'QP1212LB9FR', 'QP1208LB9FR folie', 'QP1210LB9FR folie'];

                    if (!found.isRunner) {
                        if (specialPalletsList.includes(cleanVal)) {
                            let rSelect = document.getElementById(`runnerSelect_${index}`);
                            if (rSelect && rSelect.value && rSelect.value !== 'none') {
                                rType = rSelect.value;
                            }
                        } else if (defaultRunners[cleanVal]) {
                            rType = defaultRunners[cleanVal];
                        }
                    }

                    loadItems.push({
                        pallet: found,
                        limit: stackFactor,
                        amount: amount,
                        runnerType: rType
                    });
                }
            });

            if (loadItems.length === 0) {
                alert((window.QPC_T && window.QPC_T.err_invalid) || "Please select at least one valid pallet type.");
                return;
            }

            let globalFixedItems = loadItems.filter(item => item.amount !== 'fill').map(item => ({
                ...item,
                remainingAmount: item.amount
            }));
            let fillItems = loadItems.filter(item => item.amount === 'fill');

            let trailerCount = 0;
            let trailersOutput = "";
            let globalTotals = {};
            let altContainerOutput = ""; // Alternative plan output (fill-winner when different)

            while (true) {
                trailerCount++;
                let currentTrailerOutput = "";
                let trailerHasContent = false;
                let placedAnyFixedInThisTrailer = false;

                trailer.lengths.forEach((fullFloorLength, index) => {
                    let floorLength = Math.floor(fullFloorLength * availablePercentage);
                    let marge = floorLength >= 100 ? 100 : floorLength; // Always at least 0.1m margin
                    let remainingLength = floorLength - marge;
                    let fixedOutput = "";
                    let fillOutput = "";
                    let compartmentPlacedVolume = 0;

                    let compartmentRunnersCount = {};
                    let compartmentRunnerStacks = {};
                    let palletLengthUsedMM = 0;

                    function addPalletsEstimateRunners(updates, currentRemainingLength, trailerWidth) {
                        let simCounts = { ...compartmentRunnersCount };
                        let simStacks = { ...compartmentRunnerStacks };
                        let diffLength = 0;

                        for (let u of updates) {
                            if (!u.palletItem.runnerType) continue;
                            let rTypeId = u.palletItem.runnerType;
                            let rPalletDef = runnerPallets[rTypeId];
                            let addedRunners = u.addedSpaces * u.palletItem.limit * 3;

                            let currentCount = simCounts[rTypeId] || 0;
                            let currentStacks = simStacks[rTypeId] || 0;

                            let newCount = currentCount + addedRunners;
                            let newPallets = Math.ceil(newCount / rPalletDef.perPallet);
                            let runnerLimit = trailerId === 'combi77' || trailerId === 'combi78' || trailerId === 'mega' ? rPalletDef.limitCombi : rPalletDef.limitTautliner;
                            runnerLimit = Math.max(1, Math.min(runnerLimit, Math.floor((trailer.height - MARGIN_H) / rPalletDef.h)));   // never higher than the loading space (update 38)
                            let newStacks = Math.ceil(newPallets / runnerLimit);

                            let extraStacks = newStacks - currentStacks;
                            if (extraStacks > 0) {
                                let oldL = currentStacks === 0 ? 0 : getMinimumLengthForSpaces(rPalletDef, currentStacks, trailerWidth, 999999);
                                let newL = getMinimumLengthForSpaces(rPalletDef, newStacks, trailerWidth, 999999);
                                diffLength += (newL - oldL);
                            }
                            simCounts[rTypeId] = newCount;
                            simStacks[rTypeId] = newStacks;
                        }

                        if (diffLength > currentRemainingLength) return { valid: false };
                        return { valid: true, extraLength: diffLength, newCounts: simCounts, newStacks: simStacks };
                    }

                    // 1. Place fixed items
                    globalFixedItems.forEach(item => {
                        if (item.remainingAmount <= 0) return;
                        if (trailerId.startsWith('container')) return; // handled by wall-building

                        const requiredSpaces = Math.ceil(item.remainingAmount / item.limit);
                        let spacesToPlace = 0;
                        let finalConsumed = 0;
                        let finalRunnerLength = 0;
                        let finalNewCounts = null;
                        let finalNewStacks = null;

                        for (let s = requiredSpaces; s >= 1; s--) {
                            let consumedL = getMinimumLengthForSpaces(item.pallet, s, trailer.width, remainingLength);
                            if (consumedL === null || consumedL > remainingLength) continue;

                            let runnerRes = addPalletsEstimateRunners([{ palletItem: item, addedSpaces: s }], remainingLength - consumedL, trailer.width);
                            if (runnerRes.valid) {
                                spacesToPlace = s;
                                finalConsumed = consumedL;
                                finalRunnerLength = runnerRes.extraLength;
                                finalNewCounts = runnerRes.newCounts;
                                finalNewStacks = runnerRes.newStacks;
                                break;
                            }
                        }

                        if (spacesToPlace > 0) {
                            remainingLength -= (finalConsumed + finalRunnerLength);
                            palletLengthUsedMM += finalConsumed;
                            compartmentRunnersCount = finalNewCounts;
                            compartmentRunnerStacks = finalNewStacks;

                            let placedAmount = Math.min(spacesToPlace * item.limit, item.remainingAmount);
                            let unitLabel = item.pallet.isRunner ? 'runners' : 'pcs';
                            let stackLabel = item.pallet.isRunner 
                                ? `${item.limit} runners/pos (${item.pallet.isRunner ? item.limit / item.pallet.perPallet : '?'} pallets hoog × ${item.pallet.perPallet} runners/pallet)`
                                : `${item.limit} pcs/pos`;
                            let pcsText = placedAmount === item.remainingAmount ? `${placedAmount} ${unitLabel}` : `${placedAmount} ${unitLabel} (partial)`;
                            fixedOutput += `  [Fixed Order] ${item.pallet.id} (${item.pallet.l}×${item.pallet.w}×${item.pallet.h}mm): ${pcsText} in ${spacesToPlace} position(s) — uses ${(finalConsumed / 1000).toFixed(2)}m length (stack: ${stackLabel})\n`;
                            globalTotals[item.pallet.id] = (globalTotals[item.pallet.id] || 0) + placedAmount;
                            item.remainingAmount -= placedAmount;
                            
                            // Bereken volume van de geneste vloerstapel
                            let nestedPitch = item.pallet.isCustom ? (item.pallet.isNestable ? item.pallet.nestHeight : item.pallet.h) : (2650 / item.limit);
                            compartmentPlacedVolume += placedAmount * (item.pallet.l * item.pallet.w * nestedPitch);
                            
                            trailerHasContent = true;
                            placedAnyFixedInThisTrailer = true;
                        }
                    });

                    let stillHasFixed = globalFixedItems.some(item => item.remainingAmount > 0);

                    // 2. Place Fill items (skip for containers — handled by wall-building logic below)
                    if (!stillHasFixed && fillItems.length > 0 && remainingLength > 0 && !trailerId.startsWith('container')) {
                        let fillAllocation = fillItems.map(item => ({ item, spaces: 0 }));

                        if (strategy === "all_mixes" && fillItems.length === 2 && trailer.lengths.length === 1) {
                            const ratios = [0.25, 0.50, 0.75];
                            let mixOutput = "\n  --- Available Mix Options (for remaining space) ---\n";
                            let hasMixes = false;

                            ratios.forEach(ratio => {
                                let l1 = Math.floor(remainingLength * ratio);
                                let res1 = calculateSegmentSpaces(fillItems[0].pallet, l1, trailer.width);
                                let l2 = remainingLength - res1.lengthConsumed;
                                let res2 = calculateSegmentSpaces(fillItems[1].pallet, l2, trailer.width);
                                let s1 = res1.spaces;
                                let s2 = res2.spaces;

                                while (s1 > 0 || s2 > 0) {
                                    let c1 = s1 === 0 ? 0 : getMinimumLengthForSpaces(fillItems[0].pallet, s1, trailer.width, 999999);
                                    let c2 = s2 === 0 ? 0 : getMinimumLengthForSpaces(fillItems[1].pallet, s2, trailer.width, 999999);
                                    let totalConsumed = c1 + c2;

                                    if (totalConsumed <= remainingLength) {
                                        let runnerRes = addPalletsEstimateRunners([
                                            { palletItem: fillItems[0], addedSpaces: s1 },
                                            { palletItem: fillItems[1], addedSpaces: s2 }
                                        ], remainingLength - totalConsumed, trailer.width);
                                        if (runnerRes.valid) {
                                            hasMixes = true;
                                            mixOutput += `  > Mix (${Math.round(ratio * 100)}% / ${Math.round((1 - ratio) * 100)}%):\n`;
                                            if (s1 > 0) mixOutput += `     ${fillItems[0].pallet.id} (${fillItems[0].pallet.l}×${fillItems[0].pallet.w}×${fillItems[0].pallet.h}mm): ${s1} positions, max ${s1 * fillItems[0].limit} pcs (stack: ${fillItems[0].limit} pcs/pos)\n`;
                                            if (s2 > 0) mixOutput += `     ${fillItems[1].pallet.id} (${fillItems[1].pallet.l}×${fillItems[1].pallet.w}×${fillItems[1].pallet.h}mm): ${s2} positions, max ${s2 * fillItems[1].limit} pcs (stack: ${fillItems[1].limit} pcs/pos)\n`;
                                            break;
                                        }
                                    }
                                    if (s1 > s2) s1--; else s2--;
                                }
                            });
                            if (hasMixes) {
                                fillOutput += mixOutput;
                                trailerHasContent = true;
                                remainingLength = 0;
                            }
                        } else {
                            if (strategy === "all_mixes") {
                                fillOutput += "  [Note] 'Show All Possible Mixes' works best with exactly 2 pallets on a standard trailer. Switching to iterative (fair split):\n";
                            }

                            let progress = true;
                            while (progress && remainingLength > 0) {
                                progress = false;

                                if (strategy !== "maximize_first") {
                                    fillAllocation.sort((a, b) => a.spaces - b.spaces);
                                }

                                for (let alloc of fillAllocation) {
                                    let testSpaces = alloc.spaces + 1;
                                    let consumedL = getMinimumLengthForSpaces(alloc.item.pallet, testSpaces, trailer.width, 999999);
                                    if (consumedL === null) continue;

                                    let oldConsumedL = alloc.spaces === 0 ? 0 : getMinimumLengthForSpaces(alloc.item.pallet, alloc.spaces, trailer.width, 999999);
                                    let deltaPalletL = consumedL - oldConsumedL;

                                    if (deltaPalletL > remainingLength) continue;

                                    let runnerRes = addPalletsEstimateRunners([{ palletItem: alloc.item, addedSpaces: 1 }], remainingLength - deltaPalletL, trailer.width);

                                    if (runnerRes.valid) {
                                        alloc.spaces = testSpaces;
                                        remainingLength -= (deltaPalletL + runnerRes.extraLength);
                                        palletLengthUsedMM += deltaPalletL;
                                        compartmentRunnersCount = runnerRes.newCounts;
                                        compartmentRunnerStacks = runnerRes.newStacks;
                                        progress = true;

                                        if (strategy === "maximize_first") {
                                            break;
                                        }
                                    }
                                }
                            }

                            fillAllocation.sort((a, b) => fillItems.indexOf(a.item) - fillItems.indexOf(b.item));
                            fillAllocation.forEach(alloc => {
                                if (alloc.spaces > 0) {
                                    let placedAmount = alloc.spaces * alloc.item.limit;
                                    let unitLabel = alloc.item.pallet.isRunner ? 'runners' : 'pcs';
                                    let stackLabel = alloc.item.pallet.isRunner 
                                        ? `${alloc.item.limit} runners/pos (${alloc.item.limit / alloc.item.pallet.perPallet} pallets hoog × ${alloc.item.pallet.perPallet} runners/pallet)`
                                        : `${alloc.item.limit} pcs/pos`;
                                    fillOutput += `  [Fill] ${alloc.item.pallet.id} (${alloc.item.pallet.l}×${alloc.item.pallet.w}×${alloc.item.pallet.h}mm): ${alloc.spaces} position(s) (max ${placedAmount} ${unitLabel}, stack: ${stackLabel})\n`;
                                    globalTotals[alloc.item.pallet.id] = (globalTotals[alloc.item.pallet.id] || 0) + placedAmount;
                                    
                                    // Bereken volume van de geneste vloerstapel
                                    let nestedPitch = alloc.item.pallet.isCustom ? (alloc.item.pallet.isNestable ? alloc.item.pallet.nestHeight : alloc.item.pallet.h) : (2650 / alloc.item.limit);
                                    compartmentPlacedVolume += placedAmount * (alloc.item.pallet.l * alloc.item.pallet.w * nestedPitch);
                                    
                                    trailerHasContent = true;
                                }
                            });
                        }
                    }

                    let compartmentText = fixedOutput + fillOutput;

                    let runnerOutput = "";
                    let runnerLengthUsedMM = 0;
                    Object.keys(compartmentRunnersCount).forEach(rTypeId => {
                        let count = compartmentRunnersCount[rTypeId];
                        if (count > 0) {
                            let rPallet = runnerPallets[rTypeId];
                            let numPallets = Math.ceil(count / rPallet.perPallet);
                            let numStacks = compartmentRunnerStacks[rTypeId];
                            let lengthUsedMM = getMinimumLengthForSpaces(rPallet, numStacks, trailer.width, 999999) || 0;
                            runnerLengthUsedMM += lengthUsedMM;
                            runnerOutput += `  [Runners] ${rPallet.name}: ${numPallets} pallet(s) in ${numStacks} position(s) — for ${count} runners (standard ${rPallet.perPallet} per pallet) — uses ${(lengthUsedMM / 1000).toFixed(2)}m length\n`;
                            globalTotals[rPallet.id] = (globalTotals[rPallet.id] || 0) + count;
                            trailerHasContent = true;
                        }
                    });
                    if (runnerOutput) {
                        let trueRemainingMM = fullFloorLength - palletLengthUsedMM - runnerLengthUsedMM;
                        runnerOutput += `  Remaining space: ${(fullFloorLength / 1000).toFixed(2)}m (total) − ${(palletLengthUsedMM / 1000).toFixed(2)}m (pallets) − ${(runnerLengthUsedMM / 1000).toFixed(2)}m (runners) = ${(trueRemainingMM / 1000).toFixed(2)}m\n`;
                    }

                    if (runnerOutput) compartmentText += "\n" + runnerOutput;

                    let extraPalletOutput = "";
                    if (trailerId.startsWith('container')) {
                        let fixedCandidates = globalFixedItems.filter(i => i.remainingAmount > 0);
                        let fillCandidates  = fillItems;

                        if (fixedCandidates.length > 0 || fillCandidates.length > 0) {
                            let cW = trailer.width;
                            let cH = trailer.height - MARGIN_H;
                            let cL = Math.floor((trailer.lengths ? trailer.lengths[0] : trailer.length) * availablePercentage);

                            const FILL_NORMAL_IDS = ['QP1212LB9FR','QP1212LB3RR','QP1212MB3RR','QP1212HB3RR',
                                                     'QP1311MB3R-AS','QP1311HB3R-AS','QP1311HB3R'];
                            function isFillNormal(id) { return FILL_NORMAL_IDS.includes(id); }

                            function uprightOris(pt) {
                                // Fixed-limit pallets (QP6040, 6080): ho=palletH, stackCount=1
                                // The limit (80/100/200) is applied at output time, not in wall-building
                                // Nestable LBxF: uses pallet-specific nestPitch
                                // All others: stackCount=1, ho=pt.h
                                let isFixed = pt.id.startsWith('QP6040') || pt.pallet.useFixedLimit;
                                let nestable = !isFixed && isNestableLBF(pt.id);
                                let stackCount = nestable ? getNestStackCount(pt.pallet, cH) : 1;
                                let pitch = (pt.pallet && pt.pallet.nestPitch) ? pt.pallet.nestPitch : 50;
                                let ho = isFixed ? (pt.pallet.palletH || pt.h)
                                       : nestable ? (150 + (stackCount - 1) * pitch)
                                       : pt.h;
                                return [
                                    { id: pt.id, pt, label: 'upright', br: pt.l, ho: ho, di: pt.w, isOnSide: false, stackCount },
                                    { id: pt.id, pt, label: 'rotated', br: pt.w, ho: ho, di: pt.l, isOnSide: false, stackCount },
                                ].filter(o => o.br <= cW && o.di <= cL && o.ho <= cH);
                            }
                            function onSideOris(pt) {
                                // All F-ending pallets (nestable + QP6040) may never go on their side
                                if (isNeverOnSide(pt.id)) return [];
                                return [
                                    { id: pt.id, pt, label: 'on side', br: pt.h, ho: pt.w, di: pt.l, isOnSide: true },
                                    { id: pt.id, pt, label: 'on side', br: pt.h, ho: pt.l, di: pt.w, isOnSide: true },
                                    { id: pt.id, pt, label: 'on side', br: pt.l, ho: pt.w, di: pt.h, isOnSide: true },
                                    { id: pt.id, pt, label: 'on side', br: pt.w, ho: pt.l, di: pt.h, isOnSide: true },
                                ].filter(o => o.br <= cW && o.di <= cL && o.ho <= cH);
                            }

                            function addFrontFill(colResults, types, placed) {
                                let maxUsedL = Math.max(...colResults.map(cr => cr.rows * cr.col.di));
                                let safeRestL = cL - maxUsedL;
                                if (safeRestL <= 0) return;
                                colResults.forEach(cr => {
                                    let bestN = 0, bestId = null, bestOri = null;
                                    types.forEach(pt => {
                                        let rem = pt.qty - placed[pt.id]; if (rem <= 0) return;
                                        [...uprightOris(pt), ...onSideOris(pt)].forEach(o => {
                                            if (o.di <= safeRestL && o.br <= cr.col.br) {
                                                let sc = o.stackCount || 1;
                                                let n = Math.min(Math.floor(safeRestL/o.di)*Math.floor(cr.col.br/o.br)*Math.floor(cH/o.ho)*sc, rem);
                                                if (n > bestN) { bestN = n; bestId = pt.id; bestOri = o; }
                                            }
                                        });
                                    });
                                    if (bestN > 0) {
                                        placed[bestId] += bestN;
                                        if (!cr.extras) cr.extras = [];
                                        let rows = Math.floor(safeRestL/bestOri.di);
                                        let high = Math.floor(cH/bestOri.ho);
                                        let sc = bestOri.stackCount || 1;
                                        cr.extras.push({count:bestN, id:bestId, isOnSide:bestOri.isOnSide, rows, high, di:bestOri.di, stackCount:sc});
                                        cr.extra = {count: cr.extras.reduce((s,e)=>s+e.count,0), id:bestId, isOnSide:bestOri.isOnSide};
                                    }
                                });
                            }

                            let fixedTypes = fixedCandidates.map(item => ({
                                id: item.pallet.id, pallet: item.pallet, item,
                                l: item.pallet.l,
                                w: item.pallet.w,
                                h: item.pallet.palletH || item.pallet.h,
                                // For fixed-limit pallets: qty in positions (units ÷ limit)
                                qty: (item.pallet.id.startsWith('QP6040') || item.pallet.useFixedLimit)
                                    ? Math.ceil(item.remainingAmount / item.limit)
                                    : item.remainingAmount
                            }));
                            let fillTypes = fillCandidates.map(item => ({
                                id: item.pallet.id, pallet: item.pallet, item,
                                l: item.pallet.l,
                                w: item.pallet.w,
                                h: item.pallet.palletH || item.pallet.h,
                                qty: Infinity
                            }));
                            let allTypes = [...fixedTypes, ...fillTypes];

                            // ── Runner lengte-reservering ────────────────────────────
                            let runnerReservedLength = 0;
                            let runnerColsByType = {};
                            let typesWithRunners = allTypes.filter(pt => pt.item && pt.item.runnerType);
                            let cW_orig = cW;

                            if (typesWithRunners.length > 0) {
                                let reservedL = 0;
                                for (let iter = 0; iter < 15; iter++) {
                                    let cLeff = cL - reservedL;
                                    let newReservedL = 0;
                                    let newRunnerCols = {};

                                    typesWithRunners.forEach(pt => {
                                        let rTypeId = pt.item.runnerType;
                                        let rPalletDef = runnerPallets[rTypeId];
                                        if (!rPalletDef) return;

                                        let estPallets = 0;
                                        [[pt.l, pt.w], [pt.w, pt.l]].forEach(([br, di]) => {
                                            if (br > cW) return;
                                            let cols = Math.floor(cW / br);
                                            let rows = Math.floor(cLeff / di);
                                            // For nestable LBxF: use pallet-specific nestPitch; useFixedLimit (bv. folie/QP6040): vaste palletH; others: floor(cH/h)
                                            let ptIsFixed = pt.id.startsWith('QP6040') || pt.pallet.useFixedLimit;
                                            let nestable = !ptIsFixed && isNestableLBF(pt.id);
                                            let sc = nestable ? getNestStackCount(pt.pallet, cH)
                                                              : Math.floor(cH / (ptIsFixed ? (pt.pallet.palletH || pt.h) : pt.h));
                                            let est = cols * rows * sc;
                                            if (pt.qty !== Infinity) est = Math.min(est, pt.qty);
                                            if (est > estPallets) estPallets = est;
                                        });
                                        if (estPallets <= 0) return;

                                        let totalRunners = estPallets * 3;
                                        let numRunnerPallets = Math.ceil(totalRunners / rPalletDef.perPallet);
                                        let runnerLimit = Math.max(1, Math.min(rPalletDef.limitTautliner, Math.floor(cH / rPalletDef.h)));   // container height (update 38)

                                        let bestRunnerL = Infinity;
                                        let bestRunnerInfo = null;
                                        [[rPalletDef.l, rPalletDef.w], [rPalletDef.w, rPalletDef.l]].forEach(([rBr, rDi]) => {
                                            if (rBr > cW) return;
                                            let colsInWidth = Math.floor(cW / rBr);
                                            if (colsInWidth <= 0) return;
                                            let palletsPerRow = colsInWidth * runnerLimit;
                                            let rowsNeeded = Math.ceil(numRunnerPallets / palletsPerRow);
                                            let lenNeeded = rowsNeeded * rDi;
                                            if (lenNeeded < bestRunnerL) {
                                                bestRunnerL = lenNeeded;
                                                bestRunnerInfo = { rBr, rDi, colsInWidth, rowsNeeded, numRunnerPallets, runnerLimit, estPallets, rPalletDef, totalRunners };
                                            }
                                        });

                                        if (!bestRunnerInfo || bestRunnerL >= cLeff) return;

                                        newReservedL += bestRunnerL;
                                        newRunnerCols[rTypeId] = bestRunnerInfo;
                                    });

                                    if (newReservedL === reservedL) break;
                                    reservedL = newReservedL;
                                    runnerColsByType = newRunnerCols;
                                }
                                runnerReservedLength = reservedL;
                            }

                            let cL_orig = cL;
                            cL = cL - runnerReservedLength;
                            let floorLengthAfterRunners = cL;

                            // ── KERN: Voer een volledige berekening uit voor een gegeven kolomset ──
                            function runCalc(forcedCols) {
                                let bestFixed = null, bestFill = null, bestOnSide = null;

                                if (forcedCols) {
                                    let placed = {}; allTypes.forEach(pt => placed[pt.id] = 0);
                                    let colResults = [], total = 0;
                                    let maxUsedL = 0;
                                    forcedCols.forEach(c => {
                                        let rows = c.altRijen || Math.floor(cL/c.di);
                                        let high = Math.floor(cH/c.ho);
                                        let sc = c.stackCount || 1;
                                        let cap = rows * high * sc;
                                        let rem = c.pt.qty - placed[c.id];
                                        let tp = Math.min(cap, Math.max(0, rem));
                                        placed[c.id] += tp; total += tp;
                                        let usedL = c.altUsedL || rows * c.di;
                                        let restL = cL - usedL;
                                        if (usedL > maxUsedL) maxUsedL = usedL;
                                        colResults.push({ col: c, rows, high, placed: tp, restL: Math.max(0, restL), stackCount: sc });
                                    });
                                    let safeRestLAlt = cL - maxUsedL;
                                    if (safeRestLAlt > 0) {
                                        colResults.forEach(cr => { cr.restL = safeRestLAlt; });
                                    }
                                    addFrontFill(colResults, allTypes, placed);
                                    let usedW = forcedCols.reduce((s,c)=>s+c.br,0);
                                    bestFixed = { cols: colResults, fixedTotal: total, usedWidth: usedW, placed: {...placed}, score: 0 };

                                    let restWOnSide = cW - usedW - (forcedCols.length * 5);
                                    if (restWOnSide > 0) {
                                        let onSideOpts = allTypes.flatMap(pt => onSideOris(pt));
                                        let placedAfter = {...placed};
                                        allTypes.forEach(pt => { if (placedAfter[pt.id] === undefined) placedAfter[pt.id] = 0; });
                                        let bOS = null;
                                        function recurseOS(cols, usedW2) {
                                            if (cols.length > 0) {
                                                let p2 = {...placedAfter};
                                                let cr2 = [], t2 = 0;
                                                cols.forEach(c => {
                                                    let rows = Math.floor(cL/c.di), high = Math.floor(cH/c.ho);
                                                    let sc = c.stackCount || 1;
                                                    let rem = c.pt.qty - p2[c.id];
                                                    let tp = Math.min(rows*high*sc, Math.max(0, rem));
                                                    p2[c.id] = (p2[c.id]||0)+tp; t2+=tp;
                                                    cr2.push({col:c, rows, high, placed:tp, restL:cL-rows*c.di, stackCount:sc});
                                                });
                                                addFrontFill(cr2, allTypes, p2);
                                                let ost = cr2.reduce((s,cr)=>s+cr.placed+(cr.extra?.count||0),0);
                                                if (!bOS || ost > bOS.onSideTotal) bOS = {cols:cr2.map(c=>({...c})), onSideTotal:ost, placed:{...p2}};
                                            }
                                            if (usedW2 >= restWOnSide || cols.length >= 10) return;
                                            for (const o of onSideOpts) {
                                                let tc = forcedCols.length + cols.length + 1;
                                                if (usedW + usedW2 + o.br + tc*5 <= cW) recurseOS([...cols,o], usedW2+o.br);
                                            }
                                        }
                                        recurseOS([], 0);
                                        bestOnSide = bOS;
                                    }
                                } else {
                                    // Normal upright search
                                    if (fixedTypes.length > 0) {
                                        let fixedOpts = fixedTypes.flatMap(pt => uprightOris(pt));
                                        function recurseFixed(cols, usedW) {
                                            if (cols.length > 0) {
                                                let placed = {}; fixedTypes.forEach(pt => placed[pt.id] = 0);
                                                let colResults = [], total = 0;
                                                cols.forEach(c => {
                                                    let rows = Math.floor(cL/c.di), high = Math.floor(cH/c.ho);
                                                    let sc = c.stackCount || 1;
                                                    let cap = rows*high*sc;
                                                    let rem = c.pt.qty - placed[c.id];
                                                    let tp = Math.min(cap, Math.max(0, rem));
                                                    placed[c.id] += tp; total += tp;
                                                    colResults.push({col:c, rows, high, placed:tp, restL:cL-rows*c.di, stackCount:sc});
                                                });
                                                addFrontFill(colResults, fixedTypes, placed);
                                                let ft = colResults.reduce((s,cr)=>s+cr.placed+(cr.extra?.count||0),0);
                                                let score = ft*10000+(cW-usedW);
                                                if (!bestFixed || score > bestFixed.score)
                                                    bestFixed = {cols:colResults.map(c=>({...c})), fixedTotal:ft, usedWidth:usedW, placed:{...placed}, score};
                                            }
                                            if (usedW >= cW || cols.length >= 8) return;
                                            for (const o of fixedOpts) if (usedW+o.br+(cols.length+1)*5 <= cW) recurseFixed([...cols,o], usedW+o.br);
                                        }
                                        recurseFixed([], 0);
                                    }

                                    let usedAfterFixed = bestFixed?.usedWidth || 0;
                                    let placedAfterFixed = bestFixed ? {...bestFixed.placed} : {};
                                    allTypes.forEach(pt => { if (placedAfterFixed[pt.id]===undefined) placedAfterFixed[pt.id]=0; });
                                    let fixedColCount = bestFixed?.cols.length || 0;
                                    let restWFill = cW - usedAfterFixed - fixedColCount*5;

                                    if (fillTypes.length > 0 && restWFill > 0) {
                                        let fillOpts = fillTypes.flatMap(pt => uprightOris(pt));
                                        function recurseFill(cols, usedW) {
                                            if (cols.length > 0) {
                                                let placed = {...placedAfterFixed};
                                                let colResults = [], total = 0;
                                                cols.forEach(c => {
                                                    let rows=Math.floor(cL/c.di),high=Math.floor(cH/c.ho);
                                                    let sc = c.stackCount || 1;
                                                    let tp=rows*high*sc;
                                                    placed[c.id]=(placed[c.id]||0)+tp; total+=tp;
                                                    colResults.push({col:c,rows,high,placed:tp,restL:cL-rows*c.di,stackCount:sc});
                                                });
                                                addFrontFill(colResults, fillTypes, placed);
                                                let ft = colResults.reduce((s,cr)=>s+cr.placed+(cr.extra?.count||0),0);
                                                if (!bestFill || ft > bestFill.fillTotal)
                                                    bestFill = {cols:colResults.map(c=>({...c})), fillTotal:ft, placed:{...placed}};
                                            }
                                            if (usedW >= restWFill || cols.length >= 10) return;
                                            for (const o of fillOpts) {
                                                let tc = fixedColCount+cols.length+1;
                                                if (usedAfterFixed+usedW+o.br+tc*5 <= cW) recurseFill([...cols,o], usedW+o.br);
                                            }
                                        }
                                        recurseFill([], 0);
                                    }

                                    let fillColCount = bestFill?.cols.length || 0;
                                    let usedAfterUpright = usedAfterFixed + (bestFill ? bestFill.cols.reduce((s,cr)=>s+cr.col.br,0):0);
                                    let placedAfterUpright = bestFill ? {...bestFill.placed} : {...placedAfterFixed};
                                    allTypes.forEach(pt => { if (placedAfterUpright[pt.id]===undefined) placedAfterUpright[pt.id]=0; });
                                    let totalUprightCols = fixedColCount + fillColCount;
                                    let restWOnSide = cW - usedAfterUpright - totalUprightCols*5;

                                    if (restWOnSide > 0) {
                                        let onSideOpts = allTypes.flatMap(pt => onSideOris(pt));
                                        function recurseOnSide(cols, usedW) {
                                            if (cols.length > 0) {
                                                let placed = {...placedAfterUpright};
                                                let colResults = [], total = 0;
                                                cols.forEach(c => {
                                                    let rows=Math.floor(cL/c.di),high=Math.floor(cH/c.ho);
                                                    let sc = c.stackCount || 1;
                                                    let rem=c.pt.qty-placed[c.id];
                                                    let tp=Math.min(rows*high*sc,Math.max(0,rem));
                                                    placed[c.id]=(placed[c.id]||0)+tp; total+=tp;
                                                    colResults.push({col:c,rows,high,placed:tp,restL:cL-rows*c.di,stackCount:sc});
                                                });
                                                addFrontFill(colResults, allTypes, placed);
                                                let ost = colResults.reduce((s,cr)=>s+cr.placed+(cr.extra?.count||0),0);
                                                if (!bestOnSide || ost > bestOnSide.onSideTotal)
                                                    bestOnSide = {cols:colResults.map(c=>({...c})), onSideTotal:ost, placed:{...placed}};
                                            }
                                            if (usedW >= restWOnSide || cols.length >= 10) return;
                                            for (const o of onSideOpts) {
                                                let tc = totalUprightCols+cols.length+1;
                                                if (usedAfterUpright+usedW+o.br+tc*5 <= cW) recurseOnSide([...cols,o], usedW+o.br);
                                            }
                                        }
                                        recurseOnSide([], 0);
                                    }
                                }

                                // Tally results
                                let uprightCols = [...(bestFixed?.cols||[]), ...(bestFill?.cols||[])];
                                let onSideCols  = bestOnSide?.cols || [];
                                let uprightPlaced = {}, onSidePlacedCounts = {};
                                allTypes.forEach(pt => { uprightPlaced[pt.id]=0; onSidePlacedCounts[pt.id]=0; });
                                uprightCols.forEach(cr => {
                                    uprightPlaced[cr.col.id] += cr.placed;
                                    if (cr.extras) cr.extras.forEach(e => {
                                        if (e.isOnSide) onSidePlacedCounts[e.id] = (onSidePlacedCounts[e.id]||0)+e.count;
                                        else uprightPlaced[e.id] = (uprightPlaced[e.id]||0)+e.count;
                                    });
                                });
                                onSideCols.forEach(cr => {
                                    onSidePlacedCounts[cr.col.id] += cr.placed;
                                    if (cr.extras) cr.extras.forEach(e => {
                                        if (e.isOnSide) onSidePlacedCounts[e.id]=(onSidePlacedCounts[e.id]||0)+e.count;
                                        else uprightPlaced[e.id]=(uprightPlaced[e.id]||0)+e.count;
                                    });
                                });
                                let normalTotal=0, optionalTotal=0;
                                allTypes.forEach(pt => {
                                    let u=uprightPlaced[pt.id]||0, s=onSidePlacedCounts[pt.id]||0;
                                    if (isFillNormal(pt.id)) normalTotal+=u+s;
                                    else { normalTotal+=u; optionalTotal+=s; }
                                });
                                return { uprightCols, onSideCols, uprightPlaced, onSidePlacedCounts, normalTotal, optionalTotal,
                                         totalWithOptional: normalTotal+optionalTotal };
                            }

                            // ── Bereken upright methode ──────────────────────────────
                            let resUpright = runCalc(null);

                            // ── Bereken alternating methode (alleen bij 1 niet-vierkant type) ──
                            let resAlt = null;
                            if (allTypes.length === 1 && allTypes[0].l !== allTypes[0].w) {
                                let pt = allTypes[0];
                                let altIs6040 = pt.id.startsWith('QP6040');
                                let altIsFixed = altIs6040 || (pt.pallet && pt.pallet.useFixedLimit);
                                let altNestable = !altIsFixed && isNestableLBF(pt.id);
                                let altStackCount = altNestable ? getNestStackCount(pt.pallet, cH) : 1;
                                let altPitch = (pt.pallet && pt.pallet.nestPitch) ? pt.pallet.nestPitch : 50;
                                let altHo = altIsFixed ? (pt.pallet.palletH || pt.h)
                                          : altNestable ? (150 + (altStackCount - 1) * altPitch)
                                          : pt.h;
                                let margin2 = 2*5;
                                if (pt.l+pt.w+margin2 <= cW) {
                                    function makeAltCol(breedteIs_l, startDiepte_w) {
                                        let br = breedteIs_l ? pt.l : pt.w;
                                        let d1 = startDiepte_w ? pt.w : pt.l;
                                        let d2 = startDiepte_w ? pt.l : pt.w;
                                        let pos=0, rijen=0;
                                        while(pos < cL) {
                                            let d = (rijen%2===0) ? d1 : d2;
                                            if(pos+d <= cL) { pos+=d; rijen++; } else break;
                                        }
                                        return { id:pt.id, pt, label:'alternating', br, ho:altHo, di:d1, isOnSide:false,
                                                 stackCount:altStackCount, altRijen:rijen, altUsedL:pos };
                                    }
                                    let altCol1 = makeAltCol(true,  true);
                                    let altCol2 = makeAltCol(false, false);
                                    altCol1.qty = pt.qty; altCol2.qty = pt.qty;
                                    altCol1.pt = {...pt, qty:pt.qty}; altCol2.pt = {...pt, qty:pt.qty};

                                    altCol1.rows = altCol1.altRijen;
                                    altCol2.rows = altCol2.altRijen;

                                    let forcedCols = [altCol1, altCol2].map(c => ({
                                        ...c,
                                        di: c.br === pt.l ? pt.w : pt.l,
                                    }));
                                    resAlt = runCalc(forcedCols);
                                    if (resAlt.uprightCols[0]) resAlt.uprightCols[0].col.label = `alternating (${pt.w}/${pt.l}mm)`;
                                    if (resAlt.uprightCols[1]) resAlt.uprightCols[1].col.label = `alternating (${pt.l}/${pt.w}mm)`;
                                }
                            }

                            // ── Kies winnaar op basis van upright total ──────────────
                            let winner = resUpright;
                            let loser  = resAlt;
                            let winnerName = 'Upright';
                            let loserName  = 'Alternating';
                            if (resAlt && resAlt.normalTotal > resUpright.normalTotal) {
                                winner = resAlt; loser = resUpright;
                                winnerName = 'Alternating'; loserName = 'Upright';
                            }

                            cL = cL_orig;

                            let { uprightCols, onSideCols, uprightPlaced, onSidePlacedCounts, normalTotal, optionalTotal, totalWithOptional } = winner;
                            let allCols = [...uprightCols, ...onSideCols];

                            if (normalTotal > 0 || totalWithOptional > 0) {
                                // Update remaining amounts
                                fixedTypes.forEach(pt => {
                                    let positions = (uprightPlaced[pt.id]||0) + (isFillNormal(pt.id) ? (onSidePlacedCounts[pt.id]||0) : 0);
                                    let isFixed = pt.pallet.id.startsWith('QP6040') || pt.pallet.useFixedLimit;
                                    let amt = isFixed ? positions * pt.item.limit : positions;
                                    pt.item.remainingAmount -= Math.min(amt, pt.item.remainingAmount);
                                    globalTotals[pt.id] = (globalTotals[pt.id]||0) + amt;
                                });
                                fillTypes.forEach(pt => {
                                    let positions = (uprightPlaced[pt.id]||0) + (isFillNormal(pt.id) ? (onSidePlacedCounts[pt.id]||0) : 0);
                                    let isFixed = pt.pallet.id.startsWith('QP6040') || pt.pallet.useFixedLimit;
                                    let amt = isFixed ? positions * pt.item.limit : positions;
                                    if (amt > 0) globalTotals[pt.id] = (globalTotals[pt.id]||0) + amt;
                                });

                                // Fill rate = floor area used / total floor area
                                // NOTE: must use column footprint (width × depth), NOT total pcs placed —
                                // pcs already includes vertical stacking (high) and/or nesting (stackCount),
                                // which has nothing to do with floor coverage.
                                let usedFloor = 0;
                                uprightCols.forEach(cr => {
                                    usedFloor += cr.col.br * cr.rows * cr.col.di;
                                    if (cr.extras) cr.extras.forEach(e => { usedFloor += cr.col.br * e.rows * e.di; });
                                });
                                onSideCols.forEach(cr => {
                                    usedFloor += cr.col.br * cr.rows * cr.col.di;
                                    if (cr.extras) cr.extras.forEach(e => { usedFloor += cr.col.br * e.rows * e.di; });
                                });
                                let fillRate = (usedFloor / (cW * cL) * 100).toFixed(1);
                                let isMulti = allTypes.length > 1;
                                let totalCols = allCols.length;

                                extraPalletOutput += `\n  \u2500\u2500 CONTAINER LOADING PLAN `;
                                if (resAlt) extraPalletOutput += `[${winnerName}] `;
                                extraPalletOutput += `\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n`;
                                extraPalletOutput += `  ${(cL/1000).toFixed(2)}m \u00d7 ${(cW/1000).toFixed(2)}m \u00d7 ${(cH/1000).toFixed(2)}m\n`;
                                allTypes.forEach(pt => {
                                    let dispL = pt.pallet.unitL || pt.l;
                                    let dispW = pt.pallet.unitW || pt.w;
                                    let dispH = pt.pallet.unitH || pt.h;
                                    extraPalletOutput += `  ${pt.id}: ${dispL}\u00d7${dispW}\u00d7${dispH}mm\n`;
                                });
                                extraPalletOutput += `  Margin: ${totalCols}\u00d75mm = ${totalCols*5}mm\n`;
                                extraPalletOutput += `  Load left to right, back to front:\n`;

                                let colLetter = 'A';
                                uprightCols.forEach(cr => {
                                    if (cr.placed===0 && (!cr.extras||cr.extras.length===0)) { colLetter=String.fromCharCode(colLetter.charCodeAt(0)+1); return; }
                                    let ori = cr.col.label || (cr.col.isOnSide ? 'on side' : 'upright');
                                    let idStr = isMulti ? `${cr.col.id} ` : '';
                                    let sc = cr.stackCount || 1;
                                    let highLabel = sc > 1 ? `${sc} nested (${cr.high} pos)` : `${cr.high} high`;
                                    let isFixed = cr.col.id.startsWith('QP6040') || cr.col.pt.pallet.useFixedLimit;
                                    let colPlaced = isFixed ? cr.placed * cr.col.pt.item.limit : cr.placed;
                                    extraPalletOutput += `    Col ${colLetter} \u2014 ${idStr}${ori} ${cr.col.br}mm: ${cr.rows} deep \u00d7 ${highLabel} = ${colPlaced} pcs\n`;
                                    colLetter = String.fromCharCode(colLetter.charCodeAt(0)+1);
                                });

                                // Front fill
                                let hasFront = uprightCols.some(cr => cr.extras && cr.extras.length>0);
                                if (hasFront) {
                                    let maxUsedL = Math.max(...uprightCols.map(cr=>cr.rows*cr.col.di));
                                    let safeRestL = cL - maxUsedL;
                                    let allFrontNormal = uprightCols.every(cr=>!cr.extras||cr.extras.every(e=>isFillNormal(e.id)));
                                    extraPalletOutput += allFrontNormal ? `  Front fill:\n` : `  Front fill (optional):\n`;
                                    extraPalletOutput += `  (${safeRestL}mm free space at front)\n`;
                                    let cl = 'A';
                                    uprightCols.forEach(cr => {
                                        if (cr.extras && cr.extras.length>0) {
                                            cr.extras.forEach(e => {
                                                let isNorm = isFillNormal(e.id);
                                                let pfx = isNorm ? '' : '(', sfx = isNorm ? '' : ')';
                                                let idStr = isMulti ? `${e.id} ` : '';
                                                let ori = e.isOnSide ? 'on side' : 'upright';
                                                let sc = e.stackCount || 1;
                                                let highLabel = sc > 1 ? `${sc} nested (${e.high} pos)` : `${e.high} high`;
                                                extraPalletOutput += `    Col ${cl}: ${pfx}+${e.count} pcs ${idStr}\u2014 ${e.rows} deep \u00d7 ${highLabel} (${ori}, ${e.di}mm deep)${sfx}\n`;
                                            });
                                        }
                                        cl = String.fromCharCode(cl.charCodeAt(0)+1);
                                    });
                                }

                                // Side fill
                                if (onSideCols.length>0) {
                                    let allOSNormal = onSideCols.every(cr=>isFillNormal(cr.col.id));
                                    extraPalletOutput += allOSNormal ? `  Side fill:\n` : `  Side fill (optional):\n`;
                                    onSideCols.forEach(cr => {
                                        if (cr.placed===0&&(!cr.extras||cr.extras.length===0)) { colLetter=String.fromCharCode(colLetter.charCodeAt(0)+1); return; }
                                        let idStr = isMulti ? `${cr.col.id} ` : '';
                                        let isNorm = isFillNormal(cr.col.id);
                                        let pfx = isNorm ? '' : '(', sfx = isNorm ? '' : ')';
                                        extraPalletOutput += `    ${pfx}Col ${colLetter} \u2014 ${idStr}on side ${cr.col.br}mm: ${cr.rows} deep \u00d7 ${cr.high} high = ${cr.placed} pcs${sfx}\n`;
                                        colLetter = String.fromCharCode(colLetter.charCodeAt(0)+1);
                                    });
                                }

                                extraPalletOutput += `  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n`;
                                // For fixed-limit pallets (QP6040, 6080): positions × limit = units
                                allTypes.forEach(pt => {
                                    let isFixed = pt.pallet.id.startsWith('QP6040') || pt.pallet.useFixedLimit;
                                    let lf = isFixed ? pt.item.limit : 1;
                                    let amt = (uprightPlaced[pt.id]||0) * lf;
                                    let sideAmt = (onSidePlacedCounts[pt.id]||0) * lf;
                                    if (amt>0||sideAmt>0) {
                                        extraPalletOutput += isFillNormal(pt.id)
                                            ? `  ${pt.id}: ${amt+sideAmt} pcs\n`
                                            : `  ${pt.id}: ${amt} pcs\n`;
                                    }
                                });
                                // Scale normalTotal and totalWithOptional for fixed-limit pallets (single type only)
                                let lf0 = (allTypes.length === 1 && (allTypes[0].pallet.id.startsWith('QP6040') || allTypes[0].pallet.useFixedLimit)) ? allTypes[0].item.limit : 1;
                                let displayNormal = normalTotal * lf0;
                                let displayTotal  = totalWithOptional * lf0;

                                if (optionalTotal>0)
                                    extraPalletOutput += `  TOTAL: ${displayNormal} pcs upright (with side fill: ${displayTotal} pcs) | Fill rate: ${fillRate}%\n`;
                                else
                                    extraPalletOutput += `  TOTAL: ${displayNormal} pcs | Fill rate: ${fillRate}%\n`;

                                // Method comparison
                                if (resAlt) {
                                    let uN = resUpright.normalTotal, uF = resUpright.totalWithOptional;
                                    let aN = resAlt.normalTotal,     aF = resAlt.totalWithOptional;
                                    extraPalletOutput += `\n  \u2500\u2500 Method comparison \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n`;
                                    extraPalletOutput += `  Upright:      ${uN} pcs`;
                                    if (resUpright.optionalTotal>0) extraPalletOutput += ` (with fill: ${uF})`;
                                    extraPalletOutput += `\n`;
                                    extraPalletOutput += `  Alternating:  ${aN} pcs`;
                                    if (resAlt.optionalTotal>0) extraPalletOutput += ` (with fill: ${aF})`;
                                    extraPalletOutput += `\n`;
                                    let dN = uN-aN, dF = uF-aF;
                                    if (dN===0 && dF===0) {
                                        extraPalletOutput += `  \u2192 Equal\n`;
                                    } else if (dN>=0 && dF>=0) {
                                        extraPalletOutput += `  \u2192 Upright wins (+${dN} upright${resUpright.optionalTotal>0?`, +${dF} with fill`:''})\n`;
                                    } else if (dN<=0 && dF<=0) {
                                        extraPalletOutput += `  \u2192 Alternating wins (+${-dN} upright${resAlt.optionalTotal>0?`, +${-dF} with fill`:''})\n`;
                                    } else if (dN<0 && dF>0) {
                                        extraPalletOutput += `  \u2192 Alternating wins upright (+${-dN}), Upright wins with fill (+${dF})\n`;
                                    } else {
                                        extraPalletOutput += `  \u2192 Upright wins upright (+${dN}), Alternating wins with fill (+${-dF})\n`;
                                    }

                                    let fillWinnerIsAlt = aF > uF;
                                    let fillWinnerIsUpright = uF > aF;
                                    let altIsWinner = winnerName === 'Alternating';
                                    let needsAltPlan = (altIsWinner && fillWinnerIsUpright) || (!altIsWinner && fillWinnerIsAlt);

                                    if (needsAltPlan && loser) {
                                        let lRes = loser;
                                        let lName = loserName;
                                        let lUpright = lRes.normalTotal, lFill = lRes.totalWithOptional;
                                        let diff = lFill - totalWithOptional;
                                        let altPlan = `\n  \u2500\u2500 ALTERNATIVE PLAN [${lName}] \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n`;
                                        altPlan += `  ${(cL/1000).toFixed(2)}m \u00d7 ${(cW/1000).toFixed(2)}m \u00d7 ${(cH/1000).toFixed(2)}m\n`;
                                        allTypes.forEach(pt => {
                                            let dispL = pt.pallet.unitL || pt.l;
                                            let dispW = pt.pallet.unitW || pt.w;
                                            let dispH = pt.pallet.unitH || pt.h;
                                            altPlan += `  ${pt.id}: ${dispL}\u00d7${dispW}\u00d7${dispH}mm\n`;
                                        });
                                        altPlan += `  Load left to right, back to front:\n`;
                                        let cl2 = 'A';
                                        lRes.uprightCols.forEach(cr => {
                                            if (cr.placed===0) { cl2=String.fromCharCode(cl2.charCodeAt(0)+1); return; }
                                            let ori = cr.col.label || (cr.col.isOnSide ? 'on side' : 'upright');
                                            let sc = cr.stackCount || 1;
                                            let highLabel = sc > 1 ? `${sc} nested (${cr.high} pos)` : `${cr.high} high`;
                                            altPlan += `    Col ${cl2} \u2014 ${ori} ${cr.col.br}mm: ${cr.rows} deep \u00d7 ${highLabel} = ${cr.placed} pcs\n`;
                                            cl2 = String.fromCharCode(cl2.charCodeAt(0)+1);
                                        });
                                        if (lRes.onSideCols.length > 0) {
                                            altPlan += `  Side fill (optional):\n`;
                                            lRes.onSideCols.forEach(cr => {
                                                altPlan += `    (Col ${cl2} \u2014 on side ${cr.col.br}mm: ${cr.rows} deep \u00d7 ${cr.high} high = ${cr.placed} pcs)\n`;
                                                cl2 = String.fromCharCode(cl2.charCodeAt(0)+1);
                                            });
                                        }
                                        altPlan += `  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n`;
                                        altPlan += `  TOTAL: ${lUpright} pcs upright`;
                                        if (lRes.optionalTotal > 0) altPlan += ` (with side fill: ${lFill} pcs)`;
                                        altPlan += ` | ${diff > 0 ? '+' : ''}${diff} vs winner\n`;
                                        altContainerOutput += altPlan;
                                    } else {
                                        altContainerOutput = "";
                                    }
                                }

                                // ── Runner output op basis van daadwerkelijk geplaatste pallets ──
                                let containerRunnerOutput = "";
                                if (runnerReservedLength > 0) {
                                    Object.keys(runnerColsByType).forEach(rTypeId => {
                                        let info = runnerColsByType[rTypeId];
                                        let rPalletDef = info.rPalletDef;
                                        let mainType = typesWithRunners.find(pt => pt.item.runnerType === rTypeId);
                                        let palletsPlaced = mainType ? (uprightPlaced[mainType.id] || 0) : 0;
                                        if (palletsPlaced <= 0) return;

                                        let totalRunners = palletsPlaced * 3;
                                        let numPallets = Math.ceil(totalRunners / rPalletDef.perPallet);
                                        let runnerLimit = Math.max(1, Math.min(rPalletDef.limitTautliner, Math.floor(cH / rPalletDef.h)));   // container height (update 38)
                                        let colsInWidth = info.colsInWidth;
                                        let palletsPerRow = colsInWidth * runnerLimit;
                                        let rowsNeeded = Math.ceil(numPallets / palletsPerRow);
                                        let runnerHigh = runnerLimit;
                                        let lenUsed = rowsNeeded * info.rDi;

                                        containerRunnerOutput += `  Runner wall (back of container, upright):\n`;
                                        containerRunnerOutput += `    ${colsInWidth} column(s) × ${info.rBr}mm wide, ${rowsNeeded} row(s) deep × ${runnerHigh} high = ${numPallets} pallets\n`;
                                        containerRunnerOutput += `    Length used: ${lenUsed}mm (${(lenUsed/1000).toFixed(2)}m)\n`;
                                        containerRunnerOutput += `  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n`;
                                        containerRunnerOutput += `  [Runners] ${rPalletDef.name}: ${numPallets} pallet(s) — for ${totalRunners} runners (${rPalletDef.perPallet}/pallet, last pallet may be partial)\n`;
                                        globalTotals[rPalletDef.id] = (globalTotals[rPalletDef.id] || 0) + totalRunners;
                                    });
                                    if (containerRunnerOutput) {
                                        containerRunnerOutput += `  Remaining space: ${(cL_orig / 1000).toFixed(2)}m (total) − ${(runnerReservedLength / 1000).toFixed(2)}m (runners) = ${(floorLengthAfterRunners / 1000).toFixed(2)}m\n`;
                                    }
                                }
                                if (containerRunnerOutput) {
                                    extraPalletOutput += "\n" + containerRunnerOutput;
                                }

                                trailerHasContent = true;
                                placedAnyFixedInThisTrailer = true;
                            }
                        }
                    }
                    if (extraPalletOutput) compartmentText += "\n" + extraPalletOutput;

                    if (compartmentText.trim() === "") {
                        compartmentText = "  No pallets placed in this compartment.\n";
                    }

                    let displayRemainingSpace = (remainingLength + marge) / 1000;
                    if (trailer.lengths.length > 1) {
                        currentTrailerOutput += `\n-- Compartment ${index + 1} (Remaining Space: ${displayRemainingSpace.toFixed(2)}m) --\n` + compartmentText;
                    } else if (trailerId.startsWith('container')) {
                        currentTrailerOutput += compartmentText;
                    } else {
                        currentTrailerOutput += `\n-- (Remaining Space: ${displayRemainingSpace.toFixed(2)}m) --\n` + compartmentText;
                    }
                });

                let stillHasFixed = globalFixedItems.some(item => item.remainingAmount > 0);

                if (trailerHasContent) {
                    trailersOutput += `\n=== ${trailerId.startsWith('container') ? 'CONTAINER' : 'TRAILER'} ${trailerCount} ===` + currentTrailerOutput + "\n";
                }

                if (!stillHasFixed) {
                    break;
                }

                if (!placedAnyFixedInThisTrailer && stillHasFixed) {
                    if (trailerId.startsWith('container')) {
                        break;
                    }
                    let unplaced = globalFixedItems.filter(i => i.remainingAmount > 0).map(i => i.pallet.id).join(", ");
                    trailersOutput += `\n[Error] The remaining pallets (${unplaced}) do not physically fit on the floor of this trailer. Calculation stopped.\n`;
                    break;
                }

                if (trailerCount >= 20) {
                    trailersOutput += "\n[!] Maximum of 20 trailers reached for safety. Calculation stopped.\n";
                    break;
                }
            }

            if (trailerCount > 1) {
                trailersOutput = `Total trailers required: ${trailerCount}\n` + trailersOutput;
            }

            let totalsOutput = "\n=== TOTAL LOADED PRODUCTS ===\n";
            let hasTotals = false;
            let mixWarning = (strategy === "all_mixes" && fillItems.length === 2 && trailer.lengths.length === 1);
            for (let [id, count] of Object.entries(globalTotals)) {
                totalsOutput += `  - Pallet ${id}: ${count} pcs\n`;
                hasTotals = true;
            }
            if (mixWarning) {
                totalsOutput += "  (Note: any fill from 'mix options' is not included in these totals)\n";
            }
            if (!hasTotals) {
                 totalsOutput += "  No products loaded.\n";
            }

            // Build enhanced header for print output
            const now = new Date();
            const dateOpts = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
            const headerDate = now.toLocaleDateString('en-GB', dateOpts);
            const dimL = trailer.lengths.map(l => (l / 1000).toFixed(2)).join(' + ');
            const dimW = (trailer.width / 1000).toFixed(2);
            const dimH = (trailer.height / 1000).toFixed(2);
            const pctDisplay = Math.round(availablePercentage * 100);

            let headerBlock = `════════════════════════════════════════\n`;
            headerBlock += `  Q-PALL TRUCKLOAD PLAN\n`;
            headerBlock += `════════════════════════════════════════\n`;
            headerBlock += `  Date:           ${headerDate}\n`;
            headerBlock += `  Trailer:        ${trailer.name}\n`;
            headerBlock += `  Dimensions:     ${dimL}m × ${dimW}m × ${dimH}m\n`;
            if (pctDisplay < 100) {
                headerBlock += `  Available:      ${pctDisplay}%\n`;
            }
            headerBlock += `────────────────────────────────────────\n`;

            let finalOutput = headerBlock + trailersOutput.trim() + "\n\n" + totalsOutput.trim();
            lastResult = {trailerCount, totals: globalTotals, failed: /\[Error\]|\[!\]/.test(trailersOutput), plan: finalOutput, alt: altContainerOutput.trim() ? headerBlock + altContainerOutput.trim() : ''};
            document.getElementById('outputResult').textContent = finalOutput;
            document.getElementById('resultsSection').style.display = 'block';

            // Show alternative plan if available
            const altSection = document.getElementById('altPlanSection');
            const altPre = document.getElementById('altOutputResult');
            if (altContainerOutput.trim()) {
                altPre.textContent = headerBlock + altContainerOutput.trim();
                altSection.style.display = 'block';
            } else {
                altSection.style.display = 'none';
            }
        }

/* ===== Q-Pall laadcalculator: weergave in de huisstijl van de site =====
   Draait bovenop de ongewijzigde rekenmotor (engine.js): vult diens verborgen invoervelden en roept
   calculateLoad() aan. Teksten, productnamen en de voorinstelling komen uit de pagina (#qpc-data). */
(function () {
  var root = document.getElementById('qpc'), main = document.getElementById('qpc-main'), stepsEl = document.getElementById('qpc-steps');
  var D = {}; try { D = JSON.parse(document.getElementById('qpc-data').textContent); } catch (e) {}
  var TX = D.t || {}, NICK = D.nick || {}, CAT = D.cat || {};
  window.QPC_T = TX;     // translated alert texts for engine.js (update 33)
  var t = function (k) { return TX[k] || k; };
  var nf = function (n) { return String(Math.round(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); };   // 7.500 in every language, like the rest of the site
  var esc = function (x) { return String(x).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var ICON = {
    arrow: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    back: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    check: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    plus: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    x: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    copy: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M16 8V6.5A2.5 2.5 0 0 0 13.5 4h-7A2.5 2.5 0 0 0 4 6.5v7A2.5 2.5 0 0 0 6.5 16H8" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    redo: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4.5h4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };
  var veh = function (k) { return '<svg class="qv" viewBox="0 0 168 76" aria-hidden="true"><use href="#qv-' + k + '"/></svg>'; };

  /* ---- catalogue (same sizes and versions as the original calculator) ---- */
  var SIZES = [
    { id: '1208', key: '1200x800', v: [['QP1208LB9FR', 'nest'], ['QP1208LB9FR-FOLIE', 'nest', 'foil'], ['QP1208LB3RR', 'light'], ['QP1208MB3RR', 'medium'], ['QP1208HB3RR', 'heavy'], ['EUROPAL800RR', 'heavy']] },
    { id: '1210', key: '1200x1000', v: [['QP1210LB9FR', 'nest'], ['QP1210LB9FR-FOLIE', 'nest', 'foil'], ['QP1210LB3RR', 'light'], ['QP1210MB3RR', 'medium'], ['QP1210HB3RR', 'heavy'], ['QP1210HP3R-AO', 'heavy'], ['RECYCPAL1210RR', 'heavy']] },
    { id: '1212', key: '1200x1200', v: [['QP1212LB9FR', 'nest'], ['QP1212LB3RR', 'light'], ['QP1212MB3RR', 'medium'], ['QP1212HB3RR', 'heavy']] },
    { id: '1140', key: '1140x1140', v: [['QP1140LB9FR', 'nest'], ['QP1140LB3RR', 'light'], ['QP1140MB3RR', 'medium'], ['QP1140MB3R-PAS', 'medium'], ['QP1140HB3RR', 'heavy']] },
    { id: '1111', key: '1100x1100', v: [['QP1111LB9FR', 'nest'], ['QP1111LB3RR', 'light'], ['QP1111MB3R-AS', 'medium'], ['QP1111HB3RR', 'heavy']] },
    { id: '76114', key: '760x1140', v: [['QP76114LB9FR', 'nest'], ['QP76114LB3RR', 'light']] },
    { id: '1311', key: '1300x1100', v: [['QP1311MB3R-AS', 'medium'], ['QP1311HB3R-AS', 'heavy'], ['QP1311HB3R', 'heavy']] },
    { id: '6080', key: '600x800', v: [['QP6080LR3RR', 'light'], ['QP6080M6FR', 'medium'], ['QP6080HB6FR', 'heavy']] },
    { id: '6040', key: '600x400', v: [['QP6040MB4F', 'medium'], ['QP6040HB4F', 'heavy']] }
  ];
  var dim = function (z) { return z.key.replace('x', ' x '); };
  var sub = function (z) { return NICK[z.key] || ''; };
  var sizeOf = function (sku) { return SIZES.filter(function (z) { return z.v.some(function (v) { return v[0] === sku; }); })[0]; };
  var varOf = function (sku) { return sizeOf(sku).v.filter(function (v) { return v[0] === sku; })[0]; };
  var isNest = function (sku) { return varOf(sku)[1] === 'nest'; };
  var clsOf = function (sku) { var c = varOf(sku)[1]; return c === 'nest' ? 'light' : c; };
  var img = function (sku) { return SKUIMG[sku] ? '/assets/img/pallets/' + SKUIMG[sku] + '-320.webp' : ''; };
  var RUNNER_IMG = '/assets/img/acc/click-on-runner-qp-run-l.webp';
  var NEST_RUNNER = function (sku) { return defaultRunners[sku] || 'QP-RUN-L'; };
  var badges = function (sku) {
    var v = varOf(sku), c = clsOf(sku);
    return '<span class="badge badge-' + c + '">' + t(c) + '</span>' + (v[1] === 'nest' ? '<span class="qpc-tag">' + t('nest') + '</span>' : '') + (v[2] ? '<span class="qpc-tag">' + t(v[2]) + '</span>' : '');
  };
  var label = function (sku) { var v = varOf(sku); return dim(sizeOf(sku)) + ' · ' + t(clsOf(sku)) + (v[1] === 'nest' ? ', ' + t('nest').toLowerCase() : '') + (v[2] ? ', ' + t(v[2]) : ''); };
  var siteName = function (sku) { return CAT[sku] && CAT[sku].n; };

  /* ---- state ---- */
  var PRE = root.getAttribute('data-sku') || '', PRESIZE = root.getAttribute('data-size') || '';
  // load calculator page opened from a product page: ?pallet=<calculator article number> preselects that pallet
  if (!PRE) {
    var qpal = (new URLSearchParams(location.search).get('pallet') || '').toUpperCase();
    if (qpal && sizeOf(qpal)) {
      PRE = qpal; PRESIZE = sizeOf(qpal).id;
      var art = new URLSearchParams(location.search).get('art');   // the product page's own article number, for the quote button
      if (art && /^[\w.\-]+$/.test(art)) root.setAttribute('data-site', art);
    }
  }
  if (PRE && !sizeOf(PRE)) PRE = '';
  var s = { step: 'veh', cat: null, veh: null, vehLabel: '', clen: null, ctype: 'std', size: PRESIZE || null, sku: null, mode: 'fill', qty: '', runners: true, items: [], usable: 100 };
  var STEPNO = { veh: 1, size: 2, type: 2, amt: 3, order: 3, res: 4 };

  function vehLabel() {
    if (s.cat === 'cont') return t('cont') + ' ' + s.clen + ' ' + t('ft') + (s.ctype === 'hc' ? ' high cube' : s.ctype === 'pw' ? ' pallet-wide' : '');
    return s.vehLabel;
  }
  function steps() {
    var n = STEPNO[s.step], palDone = !!(s.sku || s.items.length);
    stepsEl.innerHTML = ['s1', 's2', 's3', 's4'].map(function (k, i) {
      var st = i + 1 === n ? 'is-on' : (i + 1 < n || (i === 1 && palDone && n > 2)) ? 'is-done' : '';
      return '<li class="' + st + '"' + (i + 1 === n ? ' aria-current="step"' : '') + '><span class="qpc-n">' + (st === 'is-done' ? ICON.check : i + 1) + '</span><span class="qpc-sl">' + t(k) + '</span></li>';
    }).join('');
  }
  var head = function (title, hint) { return '<div class="qpc-head"><h3 class="qpc-h" tabindex="-1">' + title + '</h3>' + (hint ? '<p class="qpc-hint">' + hint + '</p>' : '') + '</div>'; };
  var backBtn = function (to) { return '<button type="button" class="qpc-back" data-go="' + to + '">' + ICON.back + t('back') + '</button>'; };
  var opt = function (act, val, inner, sel, tag, extra) {
    return '<button type="button" class="qpc-opt' + (sel ? ' is-sel' : '') + '" data-act="' + act + '" data-v="' + val + '" aria-pressed="' + (sel ? 'true' : 'false') + '"' + (extra || '') + '>' + (tag ? '<span class="qpc-pop">' + tag + '</span>' : '') + inner + '</button>';
  };
  var pic = function (sku) { var u = img(sku); return u ? '<img src="' + u + '" alt="" width="320" height="213" loading="lazy" decoding="async">' : ''; };
  var chip = function (act, val, txt, sel, dis) { return '<button type="button" class="qpc-chip' + (sel ? ' is-sel' : '') + '" data-act="' + act + '" data-v="' + val + '" aria-pressed="' + (sel ? 'true' : 'false') + '"' + (dis ? ' disabled' : '') + '>' + txt + '</button>'; };

  var VIEW = {
    veh: function () {
      var more = '';
      if (s.cat === 'combi') more = '<div class="qpc-more"><p class="qpc-ml">' + t('combi') + '</p><div class="qpc-chips">' + chip('veh', 'combi77', t('c77'), s.veh === 'combi77') + chip('veh', 'combi78', t('c78'), s.veh === 'combi78') + '</div></div>';
      if (s.cat === 'cont') more = '<div class="qpc-more"><p class="qpc-ml">' + t('len') + '</p><div class="qpc-chips">' + ['20', '40', '45'].map(function (l) { return chip('clen', l, l + ' ' + t('ft'), s.clen === l); }).join('') + '</div>' +
        '<p class="qpc-ml">' + t('type') + '</p><div class="qpc-chips">' + ['std', 'hc', 'pw'].map(function (k) { return chip('ctype', k, t(k), s.ctype === k, k === 'pw' && s.clen !== '45'); }).join('') + '</div>' +
        '<button type="button" class="btn btn-primary btn-sm" data-act="contgo"' + (s.clen ? '' : ' disabled') + '>' + t('next') + ICON.arrow + '</button></div>';
      var card = function (k, sel) { return opt('cat', k, veh(k) + '<span class="qpc-ot"><b>' + t(k) + '</b><small>' + t(k + '_s') + '</small></span>', sel); };
      return head(t('t_veh'), t('h_veh')) + '<div class="qpc-grid qpc-c4">' + card('taut', s.cat === 'taut') + card('mega', s.cat === 'mega') + card('combi', s.cat === 'combi') + card('cont', s.cat === 'cont') + '</div>' + more +
        '<details class="qpc-space"' + (s.usable < 100 ? ' open' : '') + '><summary>' + t('space') + '</summary><label class="qpc-range"><span>' + t('space_s') + '</span><input type="range" min="10" max="100" step="5" value="' + s.usable + '" data-act="usable" aria-label="' + esc(t('space_s')) + '"><b id="qpc-uv">' + s.usable + '%</b></label></details>';
    },
    size: function () {
      return head(t('t_size'), t('h_size')) + '<div class="qpc-grid qpc-c5">' + SIZES.map(function (z) {
        return opt('size', z.id, pic(z.v[0][0]) + '<span class="qpc-ot"><b>' + dim(z) + '</b><small>' + sub(z) + '</small></span>', s.size === z.id);
      }).join('') + '</div><div class="qpc-nav">' + backBtn('veh') + '</div>';
    },
    type: function () {
      var z = SIZES.filter(function (x) { return x.id === s.size; })[0];
      return head(t('t_type') + ' <span class="qpc-dim">' + dim(z) + ' mm</span>', t('h_type')) + '<div class="qpc-grid qpc-c' + (z.v.length === 4 || z.v.length > 6 ? 4 : 3) + '">' + z.v.map(function (v) {
        return opt('sku', v[0], pic(v[0]) + '<span class="qpc-badges">' + badges(v[0]) + '</span><span class="qpc-ot"><b>' + t('b_' + v[1]) + '</b><small>' + (siteName(v[0]) ? esc(siteName(v[0])) : v[0]) + '</small></span>', s.sku === v[0]);
      }).join('') + '</div><div class="qpc-nav">' + backBtn('size') + '</div>';
    },
    amt: function () {
      var radio = function (v, title, body) {
        return '<label class="qpc-radio' + (s.mode === v ? ' is-sel' : '') + '"><input type="radio" name="qpc-m" data-act="mode" data-v="' + v + '"' + (s.mode === v ? ' checked' : '') + '><span class="qpc-rt"><b>' + title + '</b>' + body + '</span></label>';
      };
      return head(t('t_amt'), t('h_amt')) +
        '<div class="qpc-item">' + pic(s.sku) + '<div class="qpc-it"><span class="qpc-badges">' + badges(s.sku) + '</span><b>' + label(s.sku) + '</b><small>' + (siteName(s.sku) ? esc(siteName(s.sku)) + ' · ' : '') + s.sku + '</small></div><button type="button" class="qpc-link" data-go="size">' + t('other') + '</button></div>' +
        '<div class="qpc-radios">' + radio('fill', t('fill'), '<small>' + t('fill_s') + '</small>') +
        radio('num', t('num'), '<span class="qpc-qty"><input type="number" id="qpc-qty" min="1" inputmode="numeric" value="' + esc(s.qty) + '" aria-label="' + esc(t('num')) + '"' + (s.mode === 'num' ? '' : ' disabled') + '><span>' + t('pcs') + '</span></span>') + '</div>' +
        (isNest(s.sku) ? '<label class="qpc-check' + (s.runners ? ' is-sel' : '') + '"><input type="checkbox" data-act="runners"' + (s.runners ? ' checked' : '') + '><img src="' + RUNNER_IMG + '" alt="" width="96" height="64" loading="lazy"><span class="qpc-rt"><b>' + t('runners') + '</b><small>' + t('runners_s') + '</small></span></label>' : '') +
        '<div class="qpc-nav">' + backBtn(PRE && s.sku === PRE && !s.items.length ? 'veh' : 'type') + '<button type="button" class="btn btn-primary" data-act="add">' + t('add') + ICON.arrow + '</button></div>';
    },
    order: function () {
      return head(t('t_ord'), t('h_ord')) +
        '<div class="qpc-sum"><div class="qpc-sum-veh">' + veh(s.cat || 'taut') + '<span><small>' + t('vehicle') + '</small><b>' + vehLabel() + (s.usable < 100 ? ' · ' + s.usable + '%' : '') + '</b></span><button type="button" class="qpc-link" data-go="veh">' + t('change') + '</button></div>' +
        s.items.map(function (it, i) {
          return '<div class="qpc-item">' + pic(it.sku) + '<div class="qpc-it"><span class="qpc-badges">' + badges(it.sku) + '</span><b>' + label(it.sku) + '</b><small>' + it.sku + ' · ' + (it.mode === 'fill' ? t('asmany') : nf(it.qty) + ' ' + t('pcs')) + (isNest(it.sku) ? ' · ' + t(it.runners ? 'with_r' : 'no_r') : '') + '</small></div><button type="button" class="qpc-x" data-act="del" data-v="' + i + '" aria-label="' + esc(t('remove')) + '">' + ICON.x + '</button></div>';
        }).join('') + '</div>' +
        '<div class="qpc-nav"><button type="button" class="btn btn-outline btn-sm" data-go="size">' + ICON.plus + t('addmore') + '</button><button type="button" class="btn btn-primary" data-act="calc"' + (s.items.length ? '' : ' disabled') + '>' + t('calc') + ICON.arrow + '</button></div>';
    },
    res: function () {
      var r = lastResult, isC = s.cat === 'cont', tot = r ? r.totals : {}, rows = [];
      s.items.forEach(function (it) { var got = tot[it.sku] || 0, want = it.mode === 'num' ? it.qty : null; rows.push({ sku: it.sku, n: got, short: want !== null && got < want ? want : 0 }); });
      var rn = {}; Object.keys(tot).forEach(function (k) { if (runnerPallets[k]) rn[k] = tot[k]; });
      var unit = function (n) { return n === 1 ? t(isC ? 'container' : 'truck') : t(isC ? 'containers' : 'trucks'); };
      var placed = rows.some(function (x) { return x.n > 0; });
      var anyShort = rows.some(function (x) { return x.short; }) || !placed || (r && r.failed);
      var fixedAll = s.items.every(function (i) { return i.mode === 'num'; });
      var big = !r || !placed ? '<p class="qpc-big">–</p>' : fixedAll && r.trailerCount >= 1 && !anyShort
        ? '<p class="qpc-kicker">' + t('need') + '</p><p class="qpc-big">' + r.trailerCount + ' ' + unit(r.trailerCount) + '</p>'
        : rows.length === 1 ? '<p class="qpc-kicker">' + t('fits') + '</p><p class="qpc-big">' + nf(rows[0].n) + ' <span>' + t('pallets') + '</span></p>'
        : '<p class="qpc-kicker">' + t('fits') + '</p>';
      var list = rows.map(function (x) {
        return '<li>' + pic(x.sku) + '<b class="qpc-cnt">' + nf(x.n) + '<small>×</small></b><span class="qpc-it"><b>' + label(x.sku) + '</b><small>' + x.sku + (x.short ? ' · ' + t('onlyfit').replace('{n}', nf(x.n)).replace('{m}', nf(x.short)) : '') + '</small></span></li>';
      }).join('') + Object.keys(rn).map(function (k) {
        return '<li><img src="' + RUNNER_IMG + '" alt="" width="96" height="64" loading="lazy"><b class="qpc-cnt">' + nf(rn[k]) + '<small>×</small></b><span class="qpc-it"><b>' + t('runner_l') + '</b><small>' + runnerPallets[k].name + '</small></span></li>';
      }).join('');
      var quote = quoteHref(rows, isC);
      return '<div class="qpc-res"><div class="qpc-res-top"><div><p class="qpc-res-veh">' + veh(s.cat || 'taut') + '<span>' + vehLabel() + (s.usable < 100 ? ' · ' + s.usable + '%' : '') + '</span></p>' + big + '</div></div>' +
        (anyShort ? '<p class="qpc-warn">' + (placed ? t('warn_fit') : t('warn_none')) + '</p>' : '') +
        '<ul class="qpc-list">' + list + '</ul><p class="qpc-note">' + t('note') + '</p>' +
        '<div class="qpc-actions"><a class="btn btn-primary" href="' + quote + '">' + t('contact') + ICON.arrow + '</a><button type="button" class="btn btn-ghost-light btn-sm" data-act="copy">' + ICON.copy + '<span>' + t('copy') + '</span></button><button type="button" class="btn btn-ghost-light btn-sm" data-act="again">' + ICON.redo + t('again') + '</button></div>' +
        (r && r.plan ? '<details class="qpc-plan"><summary>' + t('plan') + '</summary><pre>' + esc(r.plan) + (r.alt ? '\n\n' + esc(r.alt) : '') + '</pre></details>' : '') + '</div>' +
        '<div class="qpc-nav">' + backBtn('order') + '</div>';
    }
  };

  /* quote button: the calculated load goes along to the quote form (update 28).
     ?items=SKU:qty,SKU:qty (site article numbers; the form rounds up to full stacks) and ?note=<summary for the message field> */
  function quoteHref(rows, isC) {
    var base = root.getAttribute('data-quote') || '#', items = [], lines = [];
    rows.forEach(function (x) {
      var it = s.items.filter(function (i) { return i.sku === x.sku; })[0], n = it && it.mode === 'num' ? it.qty : x.n;
      if (!n) return;
      var site = (x.sku === PRE && root.getAttribute('data-site')) || (CAT[x.sku] && CAT[x.sku].s) || x.sku;
      items.push(site + ':' + n);
      lines.push(nf(n) + ' x ' + label(x.sku) + ' (' + site + ')');
      if (it && isNest(x.sku) && it.runners) { var rs = NEST_RUNNER(x.sku); items.push(rs + ':' + n * 3); lines.push(nf(n * 3) + ' x ' + t('runner_l') + ' (' + rs + ')'); }
    });
    if (!items.length || base === '#') return base;
    var note = t('q_note').replace('{v}', vehLabel() + (s.usable < 100 ? ' (' + s.usable + '%)' : '')) + '\n' + lines.join('\n');
    return base + (base.indexOf('?') < 0 ? '?' : '&') + 'items=' + encodeURIComponent(items.slice(0, 6).join(',')) + '&note=' + encodeURIComponent(note);
  }

  function render() { steps(); main.innerHTML = VIEW[s.step](); }
  function go(step) {
    s.step = step; render();
    var h = main.querySelector('.qpc-h, .qpc-res'); if (h) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); }
    var top = root.getBoundingClientRect().top;
    if (top < 70 || top > window.innerHeight * .6) root.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function afterVehicle() {
    if (s.items.length) return go('order');
    if (PRE) { s.sku = PRE; s.mode = 'fill'; s.qty = ''; s.runners = true; return go('amt'); }
    go(s.size ? 'type' : 'size');
  }

  /* ---- calculate: fill the engine's hidden inputs and run it (exactly like the original calculator) ---- */
  function runCalc() {
    var q = function (id) { return document.getElementById(id); };
    q('trailerSelect').value = s.veh;
    q('trailerPercentage').value = s.usable;
    q('palletRowsContainer').innerHTML = '';
    s.items.forEach(function (it) {
      addPalletRow();
      var row = q('palletRowsContainer').lastElementChild;
      row.querySelector('.pallet-select').value = pallets.filter(function (p) { return p.id === it.sku; })[0].name;
      row.querySelector('.pallet-amount').value = it.mode === 'fill' ? 'fill' : it.qty;
    });
    checkRunnersVisibility();
    s.items.forEach(function (it, i) { var sel = q('runnerSelect_' + i); if (sel) sel.value = it.runners ? NEST_RUNNER(it.sku) : 'none'; });
    lastResult = null;
    calculateLoad();
  }

  root.addEventListener('click', function (e) {
    var g = e.target.closest('[data-go]'); if (g) { go(g.getAttribute('data-go')); return; }
    var b = e.target.closest('[data-act]'); if (!b || b.disabled) return;
    var a = b.getAttribute('data-act'), v = b.getAttribute('data-v');
    if (a === 'cat') {
      s.cat = v; s.veh = null;
      if (v === 'taut' || v === 'mega') { s.veh = v === 'taut' ? 'tautliner' : v; s.vehLabel = t(v); afterVehicle(); }
      else { render(); var m = main.querySelector('.qpc-more'); if (m) m.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
    }
    else if (a === 'veh') { s.veh = v; s.vehLabel = t('combi') + ' ' + b.textContent; afterVehicle(); }
    else if (a === 'clen') { s.clen = v; if (v !== '45' && s.ctype === 'pw') s.ctype = 'std'; render(); }
    else if (a === 'ctype') { s.ctype = v; render(); }
    else if (a === 'contgo') { s.veh = 'container' + s.clen + (s.ctype === 'hc' ? 'hc' : s.ctype === 'pw' ? 'pw' : ''); afterVehicle(); }
    else if (a === 'size') { s.size = v; go('type'); }
    else if (a === 'sku') { s.sku = v; s.mode = 'fill'; s.qty = ''; s.runners = true; go('amt'); }
    else if (a === 'add') {
      var qi = document.getElementById('qpc-qty'), n = parseInt(qi.value, 10);
      if (s.mode === 'num' && !(n > 0)) { qi.focus(); qi.classList.add('is-err'); return; }
      s.items.push({ sku: s.sku, mode: s.mode, qty: s.mode === 'num' ? n : 0, runners: isNest(s.sku) && s.runners }); go('order');
    }
    else if (a === 'del') { s.items.splice(+v, 1); render(); }
    else if (a === 'calc') { runCalc(); go('res'); }
    else if (a === 'again') { s.items = []; s.cat = s.veh = null; s.clen = null; s.sku = null; s.size = PRESIZE || null; go('veh'); }
    else if (a === 'copy') {
      var txt = [vehLabel()].concat([].slice.call(main.querySelectorAll('.qpc-list li')).map(function (li) { return li.innerText.replace(/\s*\n+\s*/g, ' '); })).join('\n');
      var done = function () { var sp = b.querySelector('span'); if (sp) sp.textContent = t('copied'); };
      try { navigator.clipboard.writeText(txt).then(done, function () {}); } catch (err) {}
    }
  });
  root.addEventListener('change', function (e) {
    var el = e.target, a = el.getAttribute('data-act'); if (!a) return;
    if (a === 'mode') { var q = document.getElementById('qpc-qty'); if (q) s.qty = q.value; s.mode = el.getAttribute('data-v'); render(); if (s.mode === 'num') document.getElementById('qpc-qty').focus(); }
    else if (a === 'runners') { s.runners = el.checked; render(); }
  });
  root.addEventListener('input', function (e) {
    if (e.target.getAttribute('data-act') === 'usable') { s.usable = +e.target.value; document.getElementById('qpc-uv').textContent = s.usable + '%'; }
    if (e.target.id === 'qpc-qty') { s.qty = e.target.value; e.target.classList.remove('is-err'); }
  });
  root.classList.add('is-ready');
  render();
})();

})();
