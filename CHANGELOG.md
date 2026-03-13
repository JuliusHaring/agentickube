# CHANGELOG

<!-- version list -->

## v5.1.1 (2026-03-13)

### Bug Fixes

- Move crd into proper crd folder
  ([`706a002`](https://github.com/JuliusHaring/agentickube/commit/706a002829b3e542c45d7ecb7952bd9706008545))


## v5.1.0 (2026-03-13)

### Features

- Add networkpolicy to chart
  ([`8619a25`](https://github.com/JuliusHaring/agentickube/commit/8619a25894c85c3e97412f9851074bb2ae41b07b))

- Add system prompt as file
  ([`186fa34`](https://github.com/JuliusHaring/agentickube/commit/186fa34159e9cbfa3bed3661d23257aa1728b6a7))

### Refactoring

- Add open telemetry to agentickube level in helm chart
  ([`723514b`](https://github.com/JuliusHaring/agentickube/commit/723514b9f759c6aea5a6f78da669adade8d08fda))


## v5.0.0 (2026-03-12)

### Chores

- Replace a dataclass by a basemodel
  ([`77cdd85`](https://github.com/JuliusHaring/agentickube/commit/77cdd8543d270572825a9086e46c913712c331fe))

### Documentation

- Re-add star history chart
  ([`b896d0d`](https://github.com/JuliusHaring/agentickube/commit/b896d0d0f339dd9b2840b7a41e0c2caebf9247c6))

- Reimplement ci cd badges in readme
  ([`0a0bf82`](https://github.com/JuliusHaring/agentickube/commit/0a0bf82b84f5d820bf4ba128214df839307bf25f))

- Update readme with new features
  ([`20a2372`](https://github.com/JuliusHaring/agentickube/commit/20a2372a811f8ae022bd070a5d9f3b1554c9e4b8))

### Refactoring

- Make helm chart closer to native kubernetes
  ([`b20fd0f`](https://github.com/JuliusHaring/agentickube/commit/b20fd0f73f98bf2c12426c447408a9202ac32b55))

- Make skill discovery more verbose
  ([`5c07fd8`](https://github.com/JuliusHaring/agentickube/commit/5c07fd81778a8850c3f9d3651e831e1c9b6b93a9))

- Make skill lookup a tool
  ([`795bae5`](https://github.com/JuliusHaring/agentickube/commit/795bae5279e42bbb6aa21facdd625ae31f7ba29e))


## v4.3.0 (2026-03-12)

### Chores

- Make skills detection more verbose
  ([`8ba3d2e`](https://github.com/JuliusHaring/agentickube/commit/8ba3d2e124babe40f98892d6122b360a81ae095f))

- Remove unused functions from skills detection
  ([`7759fff`](https://github.com/JuliusHaring/agentickube/commit/7759fff85054a35c0602c7d61ded47ad6ad044fd))

### Features

- Add cleanup job
  ([`ef49439`](https://github.com/JuliusHaring/agentickube/commit/ef4943978401ec81fda7736485fdd3fa0a2592d6))

- Add metadata discovery for skills and run in bash
  ([`57bc600`](https://github.com/JuliusHaring/agentickube/commit/57bc6003eae9c1acf099d65bff69394d9ddbe84d))


## v4.2.0 (2026-03-12)

### Bug Fixes

- Fix workspace config import path
  ([`24bf103`](https://github.com/JuliusHaring/agentickube/commit/24bf1035a771dfe79fd948d6d2656632247818c5))

### Chores

- Add proper workspace skill to dev
  ([`55db8d0`](https://github.com/JuliusHaring/agentickube/commit/55db8d00c0e952a88ced7ddde22887fbd84fbf91))

### Features

- Give skills proper error handling in agent loop
  ([`c8d5e5e`](https://github.com/JuliusHaring/agentickube/commit/c8d5e5e65806cd1768b4880cf47a74d8ffa80830))

- Improve create-skill skill with its own code
  ([`d0d5e89`](https://github.com/JuliusHaring/agentickube/commit/d0d5e89e625ae34e0f102f9627d434d875def04c))

### Refactoring

- Remove brkoen create-skills skill
  ([`35f51dd`](https://github.com/JuliusHaring/agentickube/commit/35f51dd43c2596c0f9ef7909c168d6120911b335))

- Remove skills prompt
  ([`4bdc173`](https://github.com/JuliusHaring/agentickube/commit/4bdc17347791dd3db7db193023491ac9861cdaf8))


## v4.1.0 (2026-03-12)

### Chores

- Change dev agent prompt
  ([`82415f9`](https://github.com/JuliusHaring/agentickube/commit/82415f99e0b384280e7684d85ebd6da18d196722))

- Make cz check work against origin main
  ([`ac7f811`](https://github.com/JuliusHaring/agentickube/commit/ac7f8112c435361e4a4168336e1c2d5f36055b01))

### Features

- Add basic security to agent
  ([`3bf2b72`](https://github.com/JuliusHaring/agentickube/commit/3bf2b72d85e78b9c7a16f2333f5137d93388e043))

- Add keycloak to chart
  ([`6dda5da`](https://github.com/JuliusHaring/agentickube/commit/6dda5dac875e154f9e03884cc08d9b47b361b8a7))

- Add security to helm charts
  ([`f22a759`](https://github.com/JuliusHaring/agentickube/commit/f22a7591f3d74119c6e74c8c5eb033caf1b9a89b))

- Make keycloak work with proper token
  ([`9aaac2c`](https://github.com/JuliusHaring/agentickube/commit/9aaac2c0fd7ab648607962ff9a4715c13b852ddb))


## v4.0.0 (2026-03-12)

### Chores

- Add commitizen to task dev
  ([`255f155`](https://github.com/JuliusHaring/agentickube/commit/255f155932e38828b3d80200ce187d401f6f77e3))

- Run cz check only if not on main
  ([`175e201`](https://github.com/JuliusHaring/agentickube/commit/175e201815d58b95e12d0d159832ee66782838a8))

### Continuous Integration

- Add commitlint
  ([`271c835`](https://github.com/JuliusHaring/agentickube/commit/271c835628c8d71bea7609c5bdd3b26b4f88c98a))

- Make breaking change marker ! work in commit check
  ([`2da8f6e`](https://github.com/JuliusHaring/agentickube/commit/2da8f6e8ad9cb061d9231d305b05bc49a035c75b))

### Features

- Remove orchestrator entirely
  ([`dd49a60`](https://github.com/JuliusHaring/agentickube/commit/dd49a60785b5cc504cbdb3cb11370f9e8ef5ff2f))


## v3.0.3 (2026-03-12)

### Bug Fixes

- Fix typing issues - OPEN TODOs
  ([`f891048`](https://github.com/JuliusHaring/agentickube/commit/f89104807ea78879a583367aec8c3b6ea1ef9919))

### Chores

- Add ci caching
  ([`d935a9e`](https://github.com/JuliusHaring/agentickube/commit/d935a9ee28ba3800adfe41302605e9a2d771cfa5))

- Add ty for type checking
  ([`68e2e32`](https://github.com/JuliusHaring/agentickube/commit/68e2e32856375ef4a234464a6e169f1ab9b77133))

- Add ty to tasks/dev
  ([`1214620`](https://github.com/JuliusHaring/agentickube/commit/121462032ef750cb008b340891889c59d4b13173))

- Add type checking to ci
  ([`038270f`](https://github.com/JuliusHaring/agentickube/commit/038270f16050177a646e2cfbe6dc2de02f342453))

- Adjust types to match actual behaviour
  ([`696fef2`](https://github.com/JuliusHaring/agentickube/commit/696fef2e61543c867a0314331892a3b3cad158d4))

- Get rid of typing Optional
  ([`d56efb3`](https://github.com/JuliusHaring/agentickube/commit/d56efb35db8d50bfe669051464dd3457468e3115))

### Continuous Integration

- Adapt python cache paths
  ([`5c2a658`](https://github.com/JuliusHaring/agentickube/commit/5c2a6583d3e387fb00ccdab99ed1f041e3256612))


## v3.0.2 (2026-03-09)

### Bug Fixes

- Make sequence work with all agents and log any not working agents
  ([`3887fd6`](https://github.com/JuliusHaring/agentickube/commit/3887fd6318ddff3cddd332d663a88c531ee00fc2))

### Chores

- Add session id to otel spans
  ([`2acfa11`](https://github.com/JuliusHaring/agentickube/commit/2acfa1151f4fbf2be0240af38f181dcbc619204b))

### Documentation

- Add more info on commit naming and branch naming in CONTRIBUTING.md
  ([`4d13070`](https://github.com/JuliusHaring/agentickube/commit/4d13070b85ee18b5315eef3435c51a4f36907e37))

### Refactoring

- Make session_id a header
  ([`1c2bab0`](https://github.com/JuliusHaring/agentickube/commit/1c2bab011b197a65b1d6fc62eef735856f71e55d))

- Put session ids in header for orchestrator
  ([`1885461`](https://github.com/JuliusHaring/agentickube/commit/1885461fa9f2d6ace96b8a1187487af08f8e6121))


## v3.0.1 (2026-03-06)

### Bug Fixes

- Fix skill tool call signature
  ([`453cfb1`](https://github.com/JuliusHaring/agentickube/commit/453cfb17c52afcfda26aed6814cc5792cd63975c))

- Pass system prompt to agent
  ([`399320e`](https://github.com/JuliusHaring/agentickube/commit/399320e574c482c4e3fbddbca3db83b179cb9ff2))

### Chores

- Add more explicit examples
  ([`5518d24`](https://github.com/JuliusHaring/agentickube/commit/5518d24f08e98d3cbc8c74d58ac98ca1ac15b75c))

- Improve helm chart
  ([`03be645`](https://github.com/JuliusHaring/agentickube/commit/03be6452efb93782917cf1b5be7a3b59bb20e66d))

- Make internet skill fetch multiple urls if needed
  ([`cc2fb11`](https://github.com/JuliusHaring/agentickube/commit/cc2fb111f4014c2d2c086d42363a6ae7f12a76e5))

### Refactoring

- Log tool usage during usage not after
  ([`25b983e`](https://github.com/JuliusHaring/agentickube/commit/25b983e293a0bc4f5845f331c34ff60b0f39b7c6))


## v3.0.0 (2026-03-06)

### Documentation

- Add meaningful examples
  ([`78d0694`](https://github.com/JuliusHaring/agentickube/commit/78d069428ee2fc6822bbe9c79199b3aafef0b155))

### Refactoring

- Deploy helm charts instead of manifests
  ([`2773f6e`](https://github.com/JuliusHaring/agentickube/commit/2773f6e5b7bafbcb6d4d5add87912389521f5d94))


## v2.1.0 (2026-03-06)

### Bug Fixes

- Make provider use correct env var in operator
  ([`b86d9bd`](https://github.com/JuliusHaring/agentickube/commit/b86d9bd4fd11a977238e7cf8b027b0d98c589430))

### Chores

- Add recommended labels for kubernetes
  ([`ed2514a`](https://github.com/JuliusHaring/agentickube/commit/ed2514af9e427b0d3d489bc4f3b5aeb2ea75848e))

- Rename council to team
  ([`5eaecdc`](https://github.com/JuliusHaring/agentickube/commit/5eaecdc0710999e5ec64366489d98b9ac2f673a4))

### Continuous Integration

- Build images in matrix
  ([`59a1fdb`](https://github.com/JuliusHaring/agentickube/commit/59a1fdbbb3aff65706b45d719da1850385df57a9))

### Documentation

- Add MIT license
  ([`0d50d3c`](https://github.com/JuliusHaring/agentickube/commit/0d50d3ca6b0171054749343b57a955b55cb51982))

### Features

- Add otel to orchestrator
  ([`eef8f8a`](https://github.com/JuliusHaring/agentickube/commit/eef8f8ab1bbb2edd80783eb3aa8f6f5dd0e8011e))


## v2.0.0 (2026-03-06)

### Bug Fixes

- Make history work properly
  ([`f257624`](https://github.com/JuliusHaring/agentickube/commit/f25762437a29f8018c2941802b128782250f84c8))

- Make logs visible in lifespan
  ([`4a827c7`](https://github.com/JuliusHaring/agentickube/commit/4a827c72196faf75f753b87964b33849151bca96))

- Make session use same uuid format
  ([`ec4b4d1`](https://github.com/JuliusHaring/agentickube/commit/ec4b4d134539db706b9c299300230ede8f4d52b4))

- Make workspace sync work
  ([`b0ab2e3`](https://github.com/JuliusHaring/agentickube/commit/b0ab2e3e14fa4f0f7e82d252eca4c320717bcc3c))

### Chores

- Add generation pre commit hook
  ([`1d3dee5`](https://github.com/JuliusHaring/agentickube/commit/1d3dee52eb26d9c0d467c2c1e1d7361be0ad79bf))

### Documentation

- Add codeowners and contributing
  ([`4b50275`](https://github.com/JuliusHaring/agentickube/commit/4b50275818db0088fdf721456a20b9578164c405))

- Add more examples to readme
  ([`ae97798`](https://github.com/JuliusHaring/agentickube/commit/ae97798802009eb3b1d57bde00363c80d46b5689))

- Update readme with catchier intro
  ([`feac6d6`](https://github.com/JuliusHaring/agentickube/commit/feac6d67a35c9f64ea29abd4b1c3680be8754d8f))

### Features

- Add internet usage skill
  ([`2600892`](https://github.com/JuliusHaring/agentickube/commit/2600892e0d5a9d367342e3d613059826a7e5b478))

- Add orchestrator
  ([`9bd1e03`](https://github.com/JuliusHaring/agentickube/commit/9bd1e03458ea2d80d327fbff70ddd433a30959bd))

### Refactoring

- Detangle the markdown and internet skills
  ([`606fbbf`](https://github.com/JuliusHaring/agentickube/commit/606fbbf599ee481f58fa7db3546732dbb6720e7b))

- Make cli use own config
  ([`c013473`](https://github.com/JuliusHaring/agentickube/commit/c0134731b312cc44827f35523a7512f180c7fa64))

- Put history related stuff into history.py
  ([`482bf7f`](https://github.com/JuliusHaring/agentickube/commit/482bf7fd6edbe24023d5b0c2cc068baa6f1b6c33))

- Put skills in run instructions instead of user prompt
  ([`2a712ad`](https://github.com/JuliusHaring/agentickube/commit/2a712ad81e68d2c6c0d09f8a19c71e1c9ec76f4f))


## v1.11.0 (2026-03-05)

### Features

- Add job and cronjob triggers
  ([`96fceda`](https://github.com/JuliusHaring/agentickube/commit/96fceda2b1611b3bba0a5b42ab0988b20d34f37f))

### Refactoring

- Factor out non-kopf related functions from main.py in operator
  ([`6bcf04a`](https://github.com/JuliusHaring/agentickube/commit/6bcf04a46efd0d2ce7630e9498438738f1ebd91b))

- Move otel config into otel module
  ([`b3c71a8`](https://github.com/JuliusHaring/agentickube/commit/b3c71a882dc83cb43a4451383cda098a9eff9771))


## v1.10.0 (2026-03-05)

### Features

- Create crd from pydantic model
  ([`db98414`](https://github.com/JuliusHaring/agentickube/commit/db98414702146700872fd86243e93a584928026d))


## v1.9.0 (2026-03-05)

### Bug Fixes

- Make operator image work
  ([`972b72d`](https://github.com/JuliusHaring/agentickube/commit/972b72d2d5cea7c3151d837bf9d3a5ba75c13e70))

### Chores

- Make local image pull possible
  ([`fe9dff3`](https://github.com/JuliusHaring/agentickube/commit/fe9dff30f1e24696b4b9039314c97fe01ce191ef))

- Make operator use logging
  ([`09a9c72`](https://github.com/JuliusHaring/agentickube/commit/09a9c72703f1623b2df6d7b56dc8a9fe4633492f))

- Move image selection to cr
  ([`b399583`](https://github.com/JuliusHaring/agentickube/commit/b399583b6eb62fdb3beb3cd92afe71ecef95fe61))

### Features

- Deploy agent using gunicorn
  ([`9a99f1a`](https://github.com/JuliusHaring/agentickube/commit/9a99f1a351d402330a89a8c3b9fce72a7b253d9c))


## v1.8.0 (2026-03-05)

### Features

- Add entrypoint to operator
  ([`e87a9bf`](https://github.com/JuliusHaring/agentickube/commit/e87a9bf1d1b158c780a07269b0f8fd8406d857aa))


## v1.7.0 (2026-03-05)

### Features

- Add history
  ([`3f54b78`](https://github.com/JuliusHaring/agentickube/commit/3f54b789717f100276d58234d7477a1f071f37ad))


## v1.6.0 (2026-03-05)

### Bug Fixes

- Update dockerfile imports for workspace
  ([`12a9ed3`](https://github.com/JuliusHaring/agentickube/commit/12a9ed3a4bb580214e0f1a66be6331fb3f855433))

### Chores

- Add colorful unified logging
  ([`2ecf25f`](https://github.com/JuliusHaring/agentickube/commit/2ecf25f4b81c7eb9ea3f256b557b226f157a2b46))

- Update lifespan hook
  ([`4040629`](https://github.com/JuliusHaring/agentickube/commit/404062904e02b14df0f941615209619991c6dcce))

### Features

- Add mounting option for the skills
  ([`e8f183a`](https://github.com/JuliusHaring/agentickube/commit/e8f183a0fd8ad7ea47b39d6d78e6427d564bfc88))

### Refactoring

- Couple workspace and skills
  ([`b80c00a`](https://github.com/JuliusHaring/agentickube/commit/b80c00a808a2a88603d115b1b1bb1cee379dcf66))


## v1.5.0 (2026-03-05)

### Chores

- Improve task file k8s
  ([`a5ab7d6`](https://github.com/JuliusHaring/agentickube/commit/a5ab7d6adfd2c77a6870ee104afef8526fae4152))

### Features

- Add initial skills implementation
  ([`ca5fa52`](https://github.com/JuliusHaring/agentickube/commit/ca5fa5238a7395957caf2e869dd61a4720ed1453))

- Add provider choice
  ([`c1f13c7`](https://github.com/JuliusHaring/agentickube/commit/c1f13c73a7301fc843024969c5ea87870bc90ec7))

### Refactoring

- Factor out toolsets entirely
  ([`a16f8e6`](https://github.com/JuliusHaring/agentickube/commit/a16f8e6078df4a831ed6967c5cb6abf9cdb27d94))

- Prefix llm config envs with LLM_
  ([`794c336`](https://github.com/JuliusHaring/agentickube/commit/794c3361e0479f7d37c0de4a717cfb08d80c9e03))

- Rename src to code
  ([`e39f6f8`](https://github.com/JuliusHaring/agentickube/commit/e39f6f8fe9f201c730de4a7f4c587211edcc6595))


## v1.4.1 (2026-03-05)

### Bug Fixes

- Fix rbac
  ([`f1ddae2`](https://github.com/JuliusHaring/agentickube/commit/f1ddae21826e7394782eca8d92e883b519d9e753))

### Chores

- Update rbac
  ([`2d798bd`](https://github.com/JuliusHaring/agentickube/commit/2d798bda9bcf65115bcbbf234c9de7b044d5eba5))


## v1.4.0 (2026-03-05)

### Continuous Integration

- Improve cache
  ([`01f7a87`](https://github.com/JuliusHaring/agentickube/commit/01f7a878378d1f10dad61e0076477e491f191243))

### Features

- Add build platforms
  ([`149961f`](https://github.com/JuliusHaring/agentickube/commit/149961f53cfb7d0b46eea2a3a2ce87b0534a5a7c))


## v1.3.0 (2026-03-05)

### Chores

- Add badge to readme
  ([`680d36e`](https://github.com/JuliusHaring/agentickube/commit/680d36ece36930527d8a51c23f1b4c81b67bcbbb))

- Delete VERSIONING.md
  ([`1c3e798`](https://github.com/JuliusHaring/agentickube/commit/1c3e798fdc2754361365e563b8eeafd6196251a0))

- Finish release and installation strategy
  ([`4453eae`](https://github.com/JuliusHaring/agentickube/commit/4453eae5a42617b67bef28cf5c6f6b5ac6cfba41))

- Update registry to use ghcr
  ([`5bd6c39`](https://github.com/JuliusHaring/agentickube/commit/5bd6c39bb79e14d78c6736bb390c5076b57bf412))

### Continuous Integration

- Adapt dev requirements
  ([`916c11d`](https://github.com/JuliusHaring/agentickube/commit/916c11d463a21d1b8a5ce201849891f0b8f33732))

- Add ci pipeline; rename version to cd
  ([`af029c0`](https://github.com/JuliusHaring/agentickube/commit/af029c07e38c20fe049ab6ebdf9d171063546298))

- Add sha to cd
  ([`706f60a`](https://github.com/JuliusHaring/agentickube/commit/706f60a1f04f8f3cedaaed0dffba6f7f33b9a51b))

- Fix kubeconform
  ([`90466bc`](https://github.com/JuliusHaring/agentickube/commit/90466bc9b921af30acf1a7bb0bc4dc970ba83771))

- Fix sha error
  ([`ce78f4f`](https://github.com/JuliusHaring/agentickube/commit/ce78f4f26d225f30f78ba4360430c50f384d53ef))

- Parallelize docker builds
  ([`a8df83a`](https://github.com/JuliusHaring/agentickube/commit/a8df83abe8482badb0bef8f49fbac89601be445a))

- Split up ci jobs
  ([`eb07a8f`](https://github.com/JuliusHaring/agentickube/commit/eb07a8fe641a23cabc472a753e31e06edc0d47f3))

### Documentation

- Orthography
  ([`c8180a4`](https://github.com/JuliusHaring/agentickube/commit/c8180a4a75cbf13ba63cd2fb13aacf6cdc9be00a))

- Update readme
  ([`820f06e`](https://github.com/JuliusHaring/agentickube/commit/820f06eb568dcdb2d5c367605e8c449e9b6d23b3))

### Features

- Add pod config
  ([`8ba8665`](https://github.com/JuliusHaring/agentickube/commit/8ba8665b7608540e60ba2a0797935cdafde26554))


## v1.2.0 (2026-03-04)

### Chores

- Add operator own tasks
  ([`fcea9ae`](https://github.com/JuliusHaring/agentickube/commit/fcea9aecbc346b51d5bda88961c6a95d54dd95b7))

### Features

- Make image and pull policy exchangeable
  ([`e216d93`](https://github.com/JuliusHaring/agentickube/commit/e216d9303ac4f4110ac06cd66bc567fde962946a))


## v1.1.0 (2026-03-04)

### Chores

- Add examples for deployment
  ([`e9f7873`](https://github.com/JuliusHaring/agentickube/commit/e9f787316f361a5f9c67d1a825ecd1f101f9b052))

### Continuous Integration

- Add docker build and push
  ([`81216e8`](https://github.com/JuliusHaring/agentickube/commit/81216e87307cbc7dd534f78bee424a6b2ca33dad))

### Features

- Add docker for operator
  ([`7e835ba`](https://github.com/JuliusHaring/agentickube/commit/7e835ba1e961d04102249d44bb9183eba812bf9b))


## v1.0.0 (2026-03-04)

### Continuous Integration

- Add semantic release
  ([`d62bd10`](https://github.com/JuliusHaring/agentickube/commit/d62bd106faf51d0b6f21a5727e810e6b0db106b3))


## v0.1.0 (2026-03-04)

- Initial Release
