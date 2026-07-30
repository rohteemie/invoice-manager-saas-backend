import os
from weasyprint import HTML

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Professional Handyman Upskilling Academy Master Blueprint</title>
    <style>
        *, *::before, *::after {
            box-sizing: border-box;
        }
        @page {
            size: A4;
            margin: 18mm 12mm;
            background-color: #f8fafc;
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 8pt;
                color: #64748b;
            }
            @bottom-left {
                content: "Handyman Trade Academy - Master Facilitator Guide";
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 8pt;
                color: #64748b;
            }
        }
        body {
            margin: 0;
            padding: 0;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #1e293b;
        }
        h1, h2, h3, h4 {
            color: #0f172a;
            margin-top: 0;
            page-break-after: avoid;
        }
        h1 {
            font-size: 20pt;
            font-weight: 700;
            line-height: 1.2;
            color: #ffffff;
            margin-bottom: 5px;
        }
        h2 {
            font-size: 13pt;
            font-weight: 700;
            color: #1e3a8a;
            border-bottom: 2px solid #cbd5e1;
            padding-bottom: 4px;
            margin-top: 22px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        h3 {
            font-size: 11pt;
            font-weight: 700;
            color: #b45309;
            margin-top: 14px;
            margin-bottom: 6px;
        }
        p {
            margin-top: 0;
            margin-bottom: 8px;
            text-align: justify;
        }
        .header-banner {
            background-color: #1e3a8a;
            color: #ffffff;
            margin: -18mm -12mm 20px -12mm;
            padding: 22px 12mm;
            border-bottom: 4px solid #d97706;
        }
        .subtitle {
            font-size: 10pt;
            color: #93c5fd;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .meta-box {
            margin-top: 12px;
            font-size: 8.5pt;
            color: #cbd5e1;
            background-color: #1e293b;
            padding: 8px 12px;
            border-radius: 4px;
        }
        .meta-table {
            width: 100%;
            display: table;
        }
        .meta-row {
            display: table-row;
        }
        .meta-cell {
            display: table-cell;
            padding: 2px 5px;
        }
        .highlight-box {
            background-color: #f1f5f9;
            border-left: 4px solid #d97706;
            padding: 10px 14px;
            margin-bottom: 15px;
            border-radius: 0 4px 4px 0;
        }
        .highlight-box p:last-child {
            margin-bottom: 0;
        }
        .section-block {
            margin-bottom: 20px;
        }
        ul, ol {
            margin-top: 0;
            margin-bottom: 10px;
            padding-left: 18px;
        }
        li {
            margin-bottom: 4px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 9pt;
            background-color: #ffffff;
            margin-bottom: 15px;
        }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 6px 8px;
            text-align: left;
            vertical-align: top;
        }
        th {
            background-color: #1e293b;
            color: #ffffff;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 8pt;
            letter-spacing: 0.5px;
        }
        tr:nth-child(even) td {
            background-color: #f8fafc;
        }
        .badge {
            display: inline-block;
            padding: 2px 5px;
            font-size: 7pt;
            font-weight: bold;
            border-radius: 3px;
            text-transform: uppercase;
            color: #ffffff;
        }
        .badge-online { background-color: #2563eb; }
        .badge-onsite { background-color: #059669; }
        .badge-time { background-color: #475569; }
        .badge-hook { background-color: #dc2626; }
        .badge-cta { background-color: #d97706; }
        
        .time-bubble {
            font-weight: bold;
            color: #b45309;
            font-family: monospace;
        }
    </style>
</head>
<body>

    <div class="header-banner">
        <div class="subtitle">FACILITATOR MASTER GUIDE & ADVERTISING BRIEF</div>
        <h1>HIGH-INCOME HANDYMAN ACADEMY</h1>
        <div class="meta-box">
            <div class="meta-table">
                <div class="meta-row">
                    <div class="meta-cell"><strong>Format:</strong> 1-on-1 Accelerated Hybrid</div>
                    <div class="meta-cell"><strong>Target:</strong> Practicing & Aspiring Handymen (Upskilling)</div>
                </div>
                <div class="meta-row">
                    <div class="meta-cell"><strong>Focus Areas:</strong> Technical Design, Automated Budgeting, Advanced Execution</div>
                    <div class="meta-cell"><strong>Market:</strong> Nigeria (Vocational Economic Survival Model)</div>
                </div>
            </div>
        </div>
    </div>

    <div class="section-block">
        <h2>1. Strategic Shift: The Handyman Survival Model (Nigeria Focus)</h2>
        <p>This master curriculum turns street-level artisans into high-value technical contractors. Traditional formal education certificates in Nigeria focus heavily on abstract academic theory, failing to arm youth with sustainable, self-reliant skills to navigate the current economic landscape. Conversely, standard local artisans possess rough physical stamina but are completely blind to digital layout design, client brief management, and scientific material budgeting.</p>
        <p>By shifting this entire curriculum exclusively toward <strong>Aspiring Handymen and Practicing Artisans</strong>, you are delivering a direct economic lifeline. You will teach them the advanced technical foundation needed to bypass cheap field labor, communicate cleanly with high-budget corporate or residential clients, optimize material procurement to eliminate financial leakage, and run a highly professional, profitable contracting business.</p>
    </div>

    <div class="section-block">
        <h2>2. Instructor Pre-Commencement Checklist</h2>
        <p>Before launching your first live 1-on-1 training call, ensure the following core tools and administrative assets are compiled and functional:</p>
        <ul>
            <li><strong>Virtual Call Suite:</strong> A registered Zoom or Google Meet account with an integrated cloud-recording workflow so students can re-watch technical sessions.</li>
            <li><strong>Digital Workspace Assets:</strong> A standardized empty SketchUp drawing profile (.skp) configured with specific layers: <code>01_Site_Measures</code>, <code>02_Framing_Layout</code>, and <code>03_Drywall_Panels</code>.</li>
            <li><strong>Master Procurement Engine:</strong> An automated spreadsheet template containing native computational code. When a user changes square-meter values, it must update real-world item counts for local wood, boards, nails, and finishes automatically.</li>
        </ul>
    </div>

    <div class="section-block" style="page-break-before: always;">
        <h2>3. Granular Facilitator Lesson Blueprint (With Time Allocations)</h2>
        <p>This section outlines your exact timeline and talking points for every minute of the live 1-on-1 virtual training sessions. Follow the time targets strictly to keep the session organized and highly professional.</p>

        <h2>PHASE 1: DESIGN & TECHNICAL PLANNING (ONLINE 1-ON-1)</h2>
        
        <h3>Session 1: Site Logistics, MEP Alignment & Spatial Modeling | Total Duration: 90 Minutes</h3>
        <table>
            <thead>
                <tr>
                    <th style="width: 15%;">Module Timing</th>
                    <th style="width: 25%;">Topic Area</th>
                    <th style="width: 40%;">Granular Facilitator Talking Points & Core Concepts</th>
                    <th style="width: 20%;">Student Field Task</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="time-bubble">00:00 - 0:15</span><br>(15 Mins)</td>
                    <td><strong>The Technical Site Inspection</strong></td>
                    <td>Teach them how to evaluate an unrefined space. Detail structural stability checks, identifying out-of-plumb concrete structures, mapping wall dampness issues, and recognizing structural slab sagging.</td>
                    <td rowspan="3"><strong>Milestone Assignment 1:</strong><br>Student must inspect a real room, draft a clear hand-drawn site map with 8-angle reference photos, create an MEP clearance log sheet, and construct a scaled 2D canvas room model.</td>
                </tr>
                <tr>
                    <td><span class="time-bubble">0:15 - 0:35</span><br>(20 Mins)</td>
                    <td><strong>Precision Spatial Measurement</strong></td>
                    <td>How to map dimensions without compounding errors. Instruct on running laser distance paths, pulling physical tape lines under tension, cross-checking diagonal distances to verify room squareness, and recording wall heights across multiple terminal points. Teach them to photograph at least 8 distinct angles of the site for desktop reference.</td>
                </tr>
                <tr>
                    <td><span class="time-bubble">0:35 - 0:55</span><br>(20 Mins)</td>
                    <td><strong>MEP Inter-Trade Coordination</strong></td>
                    <td>Critical site management: Conducting technical alignment talks with site electricians and plumbers before touching walls. Documenting electrical box depths, marking conduit paths, and confirming water pipe clearances for false ceiling frames or wall partition depths to avoid punctures.</td>
                </tr>
                <tr>
                    <td><span class="time-bubble">0:55 - 1:30</span><br>(35 Mins)</td>
                    <td><strong>SketchUp Interface Navigation Setup</strong></td>
                    <td>Launch live screen share. Guide the student step-by-step through setting up their workspace, choosing the metric system (Millimeters), and drawing precise lines and rectangles. Teach them to use orbit, pan, and tape tools to model a 2D floor plan directly from their physical site measurements.</td>
                </tr>
            </tbody>
        </table>

        <h3>Session 2: 3D Structural Framing & Interior Sheathing Layouts | Total Duration: 90 Minutes</h3>
        <table>
            <thead>
                <tr>
                    <th style="width: 15%;">Module Timing</th>
                    <th style="width: 25%;">Topic Area</th>
                    <th style="width: 40%;">Granular Facilitator Talking Points & Core Concepts</th>
                    <th style="width: 20%;">Student Field Task</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="time-bubble">00:00 - 0:30</span><br>(30 Mins)</td>
                    <td><strong>3D Structural Framing Rules</strong></td>
                    <td>Demonstrate how to turn a 2D layout into a vertical 3D frame. Teach the strict rule of spacing studs exactly 16 inches on center (400mm O.C.). Show how to model structural components: top plates, sole plates, trimmers, and lintels around doors and windows.</td>
                    <td rowspan="2"><strong>Milestone Assignment 2:</strong><br>Student must submit a completely framed 3D room model and export an official 2D layout layout sheet displaying exact stud spacing and panel joints.</td>
                </tr>
                <tr>
                    <td><span class="time-bubble">0:30 - 1:00</span><br>(30 Mins)</td>
                    <td><strong>Digital Drywall Sheathing</strong></td>
                    <td>Show how to attach digital 4x8 foot sheets over your virtual frame. Teach structural layout rules: staggering panels to avoid continuous joints, keeping sheets 10mm off the wet floor, and planning joint seams directly over stud centers to eliminate floating edges.</td>
                </tr>
                <tr>
                    <td><span class="time-bubble">1:00 - 1:30</span><br>(30 Mins)</td>
                    <td><strong>2D Layout Layout Exports</strong></td>
                    <td>Teach the student how to push their 3D model into the 2D Layout engine. Instruct them on setting crisp orthographic scales, adding precise dimensions, and placing dynamic text callouts to make a clean, professional construction printout for job sites.</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section-block" style="page-break-before: always;">
        <h2>PHASE 2: MATERIAL PROCUREMENT & ADVANCED ESTIMATING (ONLINE 1-ON-1)</h2>
        
        <h3>Session 3: Industrial Takeoffs, Wastage Logic & Local Marketplace Indexing | Total Duration: 60 Minutes</h3>
        <table>
            <thead>
                <tr>
                    <th style="width: 15%;">Module Timing</th>
                    <th style="width: 25%;">Topic Area</th>
                    <th style="width: 40%;">Granular Facilitator Talking Points & Core Concepts</th>
                    <th style="width: 20%;">Student Field Task</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="time-bubble">00:00 - 0:20</span><br>(20 Mins)</td>
                    <td><strong>Linear & Surface Takeoffs</strong></td>
                    <td>Teach the student how to pull quantities directly from their design layout. Show how to calculate total linear meters for structural framing tracks, total face area for drywall boards, and surface area calculations for primer and paint layers.</td>
                    <td rowspan="3"><strong>Milestone Assignment 3:</strong><br>Student must fill out their master estimation spreadsheet for their custom room model, verify local material costs in their market area, and output a signed project bill of quantities (BOQ).</td>
                </tr>
                <tr>
                    <td><span class="time-bubble">0:20 - 0:40</span><br>(20 Mins)</td>
                    <td><strong>Consumable Engineering Math</strong></td>
                    <td>Break down down-market estimation formulas. Explain how to determine fastener quantities (screws spaced every 200mm), calculate tape rolls by joint lengths, and project compound weight requirements based on surface area.</td>
                </tr>
                <tr>
                    <td><span class="time-bubble">0:40 - 1:00</span><br>(20 Mins)</td>
                    <td><strong>Local Market Indexing & Wastage Matrix</strong></td>
                    <td>How to protect thin business profit margins. Introduce the mandatory 12% wastage multiplier to cover material cutting mistakes. Teach them to track current material costs at open supply markets like Odunade or local distributors to build an ironclad project budget.</td>
                </tr>
            </tbody>
        </table>

        <h2>PHASE 3: ONSITE PRACTICAL INSTALLATION BOOT CAMP (4 SESSIONS)</h2>
        <p>Students must bring their approved printouts and material budgets directly onto the physical workshop floor to complete these highly interactive field application modules.</p>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 15%;">Session Block</th>
                    <th style="width: 45%;">Hands-On Technical Tasks & Field Procedures</th>
                    <th style="width: 40%;">Core Tool Kit Mastery & Safety Standard Operating Procedures</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Session 1:<br>Framing & Site Layout</strong></td>
                    <td>
                        <ul>
                            <li>Snapping layout chalk lines on the raw floor and ceiling based on your printed blueprint details.</li>
                            <li>Cutting wood or metal framing tracks cleanly to length using hand or miter saws.</li>
                            <li>Plumb-checking and setting structural vertical studs securely inside track lines.</li>
                        </ul>
                    </td>
                    <td>
                        <ul>
                            <li><strong>Tools:</strong> Laser line projection systems, chalk reels, heavy framing squares, and impact driver drills.</li>
                            <li><strong>Safety Protocols:</strong> Mandatory use of steel-toe work boots, high-visibility vest layouts, and impact-resistant eye goggles.</li>
                        </ul>
                    </td>
                </tr>
                <tr>
                    <td><strong>Session 2:<br>Panel Hanging & First Coat</strong></td>
                    <td>
                        <ul>
                            <li>Scoring, snapping, and clean-planing raw drywall panels to fit site spatial constraints.</li>
                            <li>Hanging sheets with proper screw penetration depths, making sure screw heads sit flush without cutting the paper face.</li>
                            <li>Mixing base compound and troweling smooth joint tape across raw board intersections without leaving air pockets.</li>
                        </ul>
                    </td>
                    <td>
                        <ul>
                            <li><strong>Tools:</strong> Drywall T-squares, high-grade utility knives, material pocket routers, and 6-inch steel taping blades.</li>
                            <li><strong>Safety Protocols:</strong> Double-strap N95-rated structural dust filters must be worn during all material preparation steps.</li>
                        </ul>
                    </td>
                </tr>
                <tr>
                    <td><strong>Session 3:<br>Feathering Mud & Corners</strong></td>
                    <td>
                        <ul>
                            <li>Scraping away tool marks and imperfections from the initial dried base layer.</li>
                            <li>Applying a broader secondary coat of compound to blend and hide joints cleanly.</li>
                            <li>Mastering trowel blade pressure and hand angles to feather joint lines seamlessly into the surrounding board surface.</li>
                            <li>Installing sharp, impact-resistant external corner beads to ensure straight, clean edges.</li>
                        </ul>
                    </td>
                    <td>
                        <ul>
                            <li><strong>Tools:</strong> 10-inch and 12-inch flexible finishing trowels, specialized corner trowel blades, and clean mud boxes.</li>
                            <li><strong>Safety Protocols:</strong> Maintain a clear floor workspace, cleaning up all compound drops immediately to prevent slips and falls.</li>
                        </ul>
                    </td>
                </tr>
                <tr>
                    <td><strong>Session 4:<br>Sanding & Raking-Light Finish</strong></td>
                    <td>
                        <ul>
                            <li>Applying a final ultra-thin skim layer across the entire wall surface to equalize texture variance.</li>
                            <li>Executing final manual block sanding to achieve a perfectly flat, smooth surface.</li>
                            <li>Running the raking-light test by holding a high-intensity lamp flush against the wall face to check for shadows or flaws.</li>
                            <li>Applying professional sealer-primer, cutting sharp clean lines along corners, and rolling out a clean, uniform paint finish.</li>
                        </ul>
                    </td>
                    <td>
                        <ul>
                            <li><strong>Tools:</strong> Fine-grit hand sanding blocks, high-output LED inspection lights, premium paint rollers, and precision sash trim brushes.</li>
                            <li><strong>Safety Protocols:</strong> Strict use of sealed eye goggles and full workspace ventilation loops to protect against fine airborne sanding dust.</li>
                        </ul>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section-block" style="page-break-before: always;">
        <h2>4. High-Performance Instagram Sponsored Ad Brief</h2>
        <p>Give this section directly to your digital content creator. It contains a high-converting, attention-grabbing structure designed to stop scrolling users and drive high-intent leads to your business page.</p>

        <h3>A. Media Production Framework</h3>
        <ul>
            <li><strong>Video Target Length:</strong> Fixed between 60 and 70 seconds. The pace must be highly structured and fast-moving to hold attention.</li>
            <li><strong>The 5-Second Pattern Interrupt:</strong> Bypassing the local user's short attention span is critical. Do not start with long corporate text or static logo splash pages. Start instantly with an aggressive, highly relatable industry conflict statement paired with fast, punchy background music.</li>
            <li><strong>Visual Asset Checklist:</strong> Split-screen edits matching crisp digital 3D models directly with satisfying shots of smooth, physical tradecraft (like running a laser line level or pulling a seamless mud line with a trowel blade).</li>
        </ul>

        <h3>B. Complete 60-Second Video Script Blueprint</h3>
        <table>
            <thead>
                <tr>
                    <th style="width: 10%;">Time</th>
                    <th style="width: 15%;">Segment</th>
                    <th style="width: 40%;">Visual Action & Editing Style Directions</th>
                    <th style="width: 35%;">Voiceover (VO) Script Content & Audio Tone</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>0:00 - 0:05</strong></td>
                    <td><span class="badge badge-hook">The Hook</span></td>
                    <td>Fast, high-contrast cut showing an untidy job site with a client disputing a messy wall, cutting instantly to a sharp 3D design transforming into a flawless wall partition. <em>A strong, driving bass line drops immediately.</em></td>
                    <td><stong>"(Aggressive, high energy)* A formal certificate won't feed you in today's economy! Stop relying on basic theory and raw labor that keeps you underpaid."</strong></td>
                </tr>
                <tr>
                    <td><strong>0:05 - 0:25</strong></td>
                    <td><span class="badge badge-time">The Problem</span></td>
                    <td>Rapid, punchy cuts showing a hand spinning a 3D stud partition layout inside SketchUp, pointing at auto-updating material costs on an Excel sheet, and executing a clean trowel application over a drywall seam.</td>
                    <td><strong>"Most local handymen get undercut because they can't read blueprints, model in 3D, or budget accurately. They lose huge money on material waste and guess their way through projects."</strong></td>
                </tr>
                <tr>
                    <td><strong>0:25 - 0:45</strong></td>
                    <td><span class="badge badge-time">The Method</span></td>
                    <td>Clean split-screen view: On the left, the instructor guiding a student live via 1-on-1 video call; on the right, that exact same student confidently assembling structural wall tracks in a bright, modern workshop.</td>
                    <td><strong>"This academy fixes that. In our intensive 1-on-1 virtual training, you will master professional 3D layout design and automated procurement budgeting. Then, you step onto our workshop floor for hands-on installation boot camps."</strong></td>
                </tr>
                <tr>
                    <td><strong>0:45 - 1:00</strong></td>
                    <td><span class="badge badge-cta">The CTA</span></td>
                    <td>The instructor stands confidently in front of a finished wall segment, holding a clean finishing trowel, pointing straight down toward the screen action link box.</td>
                    <td><strong>"Build a reliable, high-income trade skill that commands premium prices from high-end clients. Spots are strictly limited due to our 1-on-1 setup. Click 'Learn More' below to claim your seat right now!"</strong></td>
                </tr>
            </tbody>
        </table>
    </div>

</body>
</html>
"""

# Write HTML content to file
input_html_path = "handyman_academy_blueprint.html"
output_pdf_path = "handyman_academy_master_blueprint.pdf"

with open(input_html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

# Convert HTML to PDF using WeasyPrint
HTML(input_html_path).write_pdf(output_pdf_path)
print(f"PDF successfully generated at: {output_pdf_path}")
