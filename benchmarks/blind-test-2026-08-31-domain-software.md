# Blind benchmark — domain expertise → software — 2026-08-31

## Purpose

Test whether Question Radar adds value beyond asking a general-purpose LLM to generate and select good questions.

The generating chat received **no repository, rubric, Question Radar vocabulary, prior corpus or master-question context**. It was asked to produce 15–25 questions about the gap between domain expertise and building software with AI, then select three questions that opened the most distinct research paths.

This benchmark is intentionally **not imported into the canonical Question Radar corpus**. It is external model output used to evaluate novelty detection, semantic overlap, lineage and editorial promotion. Treating benchmark output as canonical questions would contaminate the test.

---

## Blind output — 25 questions

1. ¿Qué parte del conocimiento de un experto es realmente traducible a software y qué parte depende demasiado del contexto, la intuición o la experiencia acumulada?
2. ¿La principal barrera es técnica o es que la mayoría de las personas nunca aprendió a pensar su trabajo como un sistema que puede descomponerse, modelarse y automatizarse?
3. ¿Cuántas personas tienen problemas suficientemente repetitivos como para justificar construir una herramienta propia?
4. ¿Qué cambia cuando programar deja de ser el cuello de botella y el cuello de botella pasa a ser definir correctamente qué construir?
5. ¿Una persona experta en un dominio sabe necesariamente especificar una buena herramienta para ese dominio?
6. ¿Qué conocimientos necesita alguien para detectar cuándo la IA está construyendo algo incorrecto aunque el software aparentemente funcione?
7. ¿Hasta qué punto el código generado por IA reduce la dependencia de programadores y hasta qué punto simplemente desplaza esa dependencia hacia arquitectura, testing, seguridad y mantenimiento?
8. ¿Qué sucede cuando alguien puede construir una aplicación pero no sabe desplegarla, mantenerla, actualizarla o proteger sus datos?
9. ¿La dificultad está en construir el primer prototipo o en atravesar el enorme salto entre “funciona en mi computadora” y “otra persona puede confiar en esto todos los días”?
10. ¿Cuántas herramientas potencialmente valiosas nunca aparecen porque quien conoce el problema no se considera a sí mismo una persona capaz de crear tecnología?
11. ¿Quién decide qué partes de una profesión deberían automatizarse: quien hace el trabajo, quien paga por el trabajo o quien construye el software?
12. ¿Qué incentivos tiene un empleado para automatizar una tarea si esa automatización puede reducir el valor percibido de su propio puesto?
13. ¿Qué incentivos tiene una empresa para permitir que sus trabajadores construyan herramientas si después tiene que hacerse responsable de software que nadie del área de IT controla?
14. ¿Qué pasa con el conocimiento institucional cuando una herramienta crítica fue construida por una sola persona usando IA y esa persona abandona la organización?
15. ¿Podría aparecer una nueva clase de trabajador cuyo principal valor no sea programar ni dominar una disciplina, sino conectar conocimiento de dominio, datos, software e IA?
16. ¿Estamos sobreestimando cuánto quiere la gente construir herramientas y subestimando cuánto prefiere simplemente tener una herramienta que funcione?
17. ¿Cuánto cuesta realmente construir software con IA cuando se incluyen mantenimiento, errores, infraestructura, seguridad, soporte y tiempo de aprendizaje?
18. ¿Qué problemas pequeños, locales o extremadamente específicos ahora podrían ser económicamente viables porque el coste de desarrollar software cayó drásticamente?
19. ¿Qué mercados nunca fueron atendidos por software porque eran demasiado pequeños para una empresa tradicional, pero podrían ser atendidos por quienes trabajan dentro de esos mismos mercados?
20. ¿Qué diferencia existe entre automatizar una tarea y capturar el modelo mental de la persona que sabe hacerla bien?
21. ¿Qué profesiones tienen conocimiento suficientemente estructurado como para beneficiarse primero de esta capacidad y cuáles dependen demasiado de conocimiento tácito?
22. ¿Qué errores aparecen cuando una persona intenta formalizar un proceso que en realidad funciona precisamente porque los humanos hacen excepciones constantemente?
23. ¿La proliferación de herramientas hechas por expertos de dominio produciría mejores sistemas especializados o un ecosistema inmanejable de pequeños softwares incompatibles?
24. ¿Qué tendría que cambiar en educación para que construir una pequeña herramienta digital fuera percibido como una habilidad básica de resolución de problemas y no como una especialidad llamada “programación”?
25. ¿Y si la premisa está equivocada y el cambio realmente importante no es que millones de expertos vayan a construir software, sino que puedan describir suficientemente bien sus problemas para que otros agentes lo construyan por ellos?

---

## Blind model selection

The generating model selected:

1. **Q4** — programming stops being the bottleneck; defining what to build becomes the bottleneck.
2. **Q12** — employee incentives to automate work that may reduce the perceived value of their role.
3. **Q18** — small/local/specific problems becoming economically viable after software-development cost falls.

Its rationale was that these open distinct paths in intellectual work/specification, organizational incentives/power, and product economics.

---

# Question Radar interpretation

## A. Strong convergence with the existing corpus

### Q4 is already represented at master level

Blind Q4:

> ¿Qué cambia cuando programar deja de ser el cuello de botella y el cuello de botella pasa a ser definir correctamente qué construir?

Existing master extension `M-20260831-02`:

> **Si construir código se vuelve barato, ¿qué pasa a ser el verdadero cuello de botella?**

This is a positive result: an independent blind generation converged on a question that the existing pipeline had already promoted. But it also shows why copying an LLM's “top questions” directly into the master library would create semantic duplication.

### Q1/Q5/Q20/Q21/Q22 cluster around an existing master

These questions all refine or challenge `M-20260831-01`:

> **¿Cuál es la brecha entre conocer profundamente un dominio y poder representarlo como un sistema ejecutable?**

Useful explicit lineage candidates:

- Q1 → `operationalizes` the tacit/explicit boundary.
- Q5 → `challenges_assumption` that domain expertise implies specification skill.
- Q20 → `refines` the difference between task automation and mental-model capture.
- Q21 → `operationalizes` domain comparison by tacit-knowledge dependence.
- Q22 → `challenges_assumption` that processes can be formalized without losing exception handling.

This cluster should not become five new master questions.

### Q14 converges with existing organizational-memory questions

Q14 asks what happens when critical software and institutional knowledge depend on one person. The master library already asks how an organization avoids rediscovering tomorrow what someone learned yesterday. Q14 is a concrete software/AI operationalization, not a new master axis.

### Q11 converges with existing power/governance questions

Q11 asks who gets to decide what parts of a profession are automated. The master library already contains `¿Quién decide?`, `¿Quién conserva capacidad de decisión?`, and questions about who designs, finances and uses technology. Q11 is valuable as a domain-specific operationalization.

---

## B. New high-value branches

### New branch 1 — incentives and self-automation

Blind Q12:

> ¿Qué incentivos tiene un empleado para automatizar una tarea si esa automatización puede reducir el valor percibido de su propio puesto?

This is not adequately represented by the current five Aug-31 master extensions. It connects automation, labor incentives, power and adoption.

**Candidate generalization:**

> **¿Qué incentivos hacen que una persona quiera —o no quiera— automatizar parte de su propio trabajo?**

This survives the specific employer/employee case while preserving the conflict between productivity and perceived role value.

Status: **candidate for master promotion, not automatically promoted by this benchmark**.

### New branch 2 — long-tail software economics

Blind Q18/Q19:

> ¿Qué problemas pequeños, locales o extremadamente específicos ahora podrían ser económicamente viables porque el coste de desarrollar software cayó drásticamente?

> ¿Qué mercados nunca fueron atendidos por software porque eran demasiado pequeños para una empresa tradicional...?

These form one economic/product lineage.

**Candidate generalization:**

> **¿Qué problemas se vuelven económicamente viables cuando cae el costo de construir software?**

This is broader than “what business can I build?” and creates a research path around long-tail markets, local software and micro-products.

Status: **candidate for master promotion, not automatically promoted by this benchmark**.

### New branch 3 — governance of user-built software / shadow IT

Blind Q13:

> ¿Qué incentivos tiene una empresa para permitir que sus trabajadores construyan herramientas si después tiene que hacerse responsable de software que nadie del área de IT controla?

This adds a governance boundary missing from the current Aug-31 promotions: democratized construction can create ownership, security, maintenance and accountability problems.

**Candidate generalization:**

> **¿Quién se hace responsable cuando construir software deja de estar limitado a los equipos de software?**

Status: strong research candidate; needs comparison with existing governance/power corpus before promotion.

### New branch 4 — ecosystem fragmentation

Blind Q23:

> ¿La proliferación de herramientas hechas por expertos de dominio produciría mejores sistemas especializados o un ecosistema inmanejable de pequeños softwares incompatibles?

This directly challenges the optimistic version of software democratization.

Potential relation: `challenges_assumption` of the “lower software cost → more useful domain tools” thesis.

Status: strong systemic-risk question; likely derivative of the existing `¿Estamos integrando o fragmentando información?`, but with a new software-ecosystem mechanism.

### New branch 5 — challenge to the core premise

Blind Q25:

> ¿Y si la premisa está equivocada y el cambio realmente importante no es que millones de expertos vayan a construir software, sino que puedan describir suficientemente bien sus problemas para que otros agentes lo construyan por ellos?

This is especially important because the blind model did **not** select it in its top three, yet Question Radar should preserve it as a high-value `challenges_assumption` relation.

It protects the investigation against confirmation bias: perhaps democratized software does not mean “everyone becomes a builder”; perhaps it means a new interface between domain description and software-producing agents.

Status: **must preserve as explicit challenge even if not promoted to master**.

---

## C. Useful but peripheral / operational branches

- Q2: systems thinking / modelability literacy.
- Q3: recurrence threshold for justifying a custom tool.
- Q6: verification literacy for apparently working AI-generated software.
- Q7/Q8/Q9/Q17: lifecycle, production readiness, infrastructure, security, maintenance and total cost.
- Q10: self-efficacy / identity as a technology creator.
- Q15: emergence of integrator/hybrid roles.
- Q16: users may prefer consuming tools rather than building them.
- Q24: education and tool-building literacy.

These are useful research questions, but they do not all belong at master level.

---

# Benchmark result

## What the blind model did well

- generated broad thematic diversity;
- independently rediscovered an existing master-level bottleneck question;
- surfaced two genuinely new high-value paths in incentives and long-tail economics;
- included several strong challenges to the original premise.

## What Question Radar adds

### 1. Corpus-relative novelty

A question can be excellent and still be redundant. Blind Q4 is a strong question but already represented by `M-20260831-02`.

### 2. Lineage instead of list accumulation

Q1, Q5, Q20, Q21 and Q22 are not five unrelated “great questions”; they form a family around the domain-knowledge → executable-system transition.

### 3. Preservation of challenge questions

Blind Q25 was not selected by the generating model, but it is structurally important because it challenges the core premise.

### 4. Separation of master questions from operational cases

Recruiting, GitHub, IT governance, deployment and employee incentives can remain concrete cases without forcing every domain-specific formulation into the master core.

### 5. Human-review boundary

The benchmark does **not** automatically promote Q12, Q18 or Q25. It surfaces them as candidates with explicit reasons. Editorial promotion remains a revisable human judgment.

---

# Provisional benchmark verdict

**PASS — Question Radar adds information that the blind LLM selection alone does not provide.**

The strongest evidence is not that Question Radar finds “better” questions. It is that it can distinguish:

```text
good + already represented
good + refines an existing question
good + challenges an assumption
good + opens a genuinely new research branch
good + operational but not master-level
```

For this benchmark:

- blind top-3 question Q4 = **high quality, low novelty, strong convergence**;
- blind top-3 Q12 = **high quality, high novelty, incentives/power branch**;
- blind top-3 Q18 = **high quality, high novelty, economics/product branch**;
- non-selected Q25 = **high structural value as a premise challenge**.

That difference is the core utility being tested.

---

## Next benchmark

Use the same blind procedure on a very different domain (for example education, geology, healthcare operations, logistics or public administration) and test whether the system still separates semantic novelty from merely strong wording.
