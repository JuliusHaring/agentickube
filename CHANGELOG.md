# CHANGELOG

<!-- version list -->

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
