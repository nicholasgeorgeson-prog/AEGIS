AEGIS Cinematic Loader Pack (GSAP-only now, Rive-ready)

Contents:
- index_snippet.html : loader container + includes
- cinematic-loader.css : styling
- cinematic-loader.js : loader module
- aegis_loader_28px.svg : Rive starter asset (28px bar)
- AEGIS_Cinematic_Loader_Pack_v1.docx : single handoff document (same content)

Integration:
1) Include GSAP: /static/js/vendor/gsap.min.js
2) Include cinematic-loader.css and cinematic-loader.js
3) Paste HTML snippet into your template.
4) Mount:
   const loader = CinematicLoader.mount('#aegisLoader', { fps: 30, maxDpr: 1.5 });
   loader.setProgress(0.25);
   loader.complete();

Rive later:
- Build aegis_loader.riv using the SVG and the spec in the DOCX.
- State machine: LoaderSM
- Inputs: progress (0..100), done (trigger), error (trigger optional)
