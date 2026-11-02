# Source10 candidate fix wave 1

Base 6b1e07c8318a334ee1f2218863eb84254e38f526 → commit 118ba152b007c30d358c8bc44c51aabe8ae820f0 on codex/jarvis-work-navigation-v3-source10. One combined implementation commit. The tracked worktree and index are clean.

## C1 — original deadline at publication

WorkService calls the research ledger’s existing admit_ack after real final packet and artifact verification and source selection, immediately before publishing succeeded. It samples the original monotonic deadline even after the runner sealed the ledger. The ordinary exception path retains the completed effect, its verified artifact and public identities, and returns needs_attention. There is no replay, extra transport request or new deadline.

The parametrized test uses actual SDK navigation, mock inference transport, configured Guardrails, browser fixture, writer and filesystem. All author and ACK requests ran at controlled time 0 with deadline 260. The wrapper first calls the original verifier and retains its result, then advances time after the real final readback. The frozen-before/after sample includes the path, digest and dispatch, report, adapter and file IDs. All three cases sent exactly 15 requests (5 chat generations), kept one completed effect and one reopened file. The first RED passed before the boundary but returned succeeded incorrectly at and after it. Final reopening yielded:

- before 259.99999999999994 — succeeded, error None, SHA-256 d02d4922394a206a6dcbaf4c4ec1d814d557e0a93f46757e84e5d93cc56e6f53, file H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\temp\test_service_deadline_after_fi0\00000000-0000-0000-0000-0000000003e8\research.md, report 00000000-0000-0000-0000-000000000401, file ID 00000000-0000-0000-0000-000000000403, dispatch 00000000-0000-0000-0000-000000000400, adapter 00000000-0000-0000-0000-000000000402.
- at 260 — needs_attention, error 'Research acknowledgement deadline', SHA-256 d02d4922394a206a6dcbaf4c4ec1d814d557e0a93f46757e84e5d93cc56e6f53, file H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\temp\test_service_deadline_after_fi1\00000000-0000-0000-0000-0000000003e8\research.md, report 00000000-0000-0000-0000-000000000401, file ID 00000000-0000-0000-0000-000000000403, dispatch 00000000-0000-0000-0000-000000000400, adapter 00000000-0000-0000-0000-000000000402.
- after 260.00000000000006 — needs_attention, error 'Research acknowledgement deadline', SHA-256 d02d4922394a206a6dcbaf4c4ec1d814d557e0a93f46757e84e5d93cc56e6f53, file H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\temp\test_service_deadline_after_fi2\00000000-0000-0000-0000-0000000003e8\research.md, report 00000000-0000-0000-0000-000000000401, file ID 00000000-0000-0000-0000-000000000403, dispatch 00000000-0000-0000-0000-000000000400, adapter 00000000-0000-0000-0000-000000000402.

## C2 — validate the final answer before promotion

The view checks for a nonblank parsed final after schema, configured scanning, raw equality and transport return checks, before assigning the secured envelope or promoting the pending page. The fourth raw chat response in the new matrix case is a one-space final; it passes through the actual parser and guard, without the history/schema mutation branch. The first RED produced the intended Empty research final answer error yet promoted pages [1, 2, 3]. GREEN confirms only [1, 2], three genuine inspect START/END pairs, four attempted generations, three secured timeline entries, no fourth dispatch, write effect, file or final runtime proof. The four valid writer chains passed.

## Test process receipts

Evidence root H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code. Each receipt binds the invocation, environment, times, stdout, stderr, JUnit and source maps. The fixed -B -X utf8 H venv runner hash is 60f6ea3d157969dcaa4eebef474a62642da6f02963cb8a87b405217f788ac32c. Each test receipt was independently reopened and rehashed. Ordered invocations and output identities follow.

### c1-red

Receipt H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c1-red\receipt.json SHA-256 800160410f937c58e496b2e956dac9b75dfee32edc5efb30bbbefab2888997e6

H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 -m pytest src/brain/tests/test_work_navigation_transport.py::test_service_deadline_after_final_readback -q -p no:cacheprovider -p ultima_nav_pathcheck --basetemp=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c1-red\temp --junitxml=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c1-red\junit.xml

2 failed, 1 passed in 5.03s

{"invocation.json": "0ea868a83c3cdf422dca3fa330bc14ee1d16441bde051fbb1d2ed9c77954726e", "junit.xml": "b7e2e4c07d184b2bfd2050474cfef36c425ffa9a7990613f6e45f183826c51e6", "loaded-paths.json": "80a41fabb06ae137d6281cc8cce5b246875eee5637f94d104430de6e9e0afe65", "stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stdout.log": "d41473101b6e793392aa66b7725c7046ad8f43787b7d2ca1c561e4a8832611d9", "ultima_nav_pathcheck.py": "88adfb44f6a64ef460a31586178204ffba0925e956e30934132a9a0bf2263548"}

### c1-green

Receipt H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c1-green\receipt.json SHA-256 0197adfef40a3d5b4d63a3845efae49534deafc723966475c883e26a08c7ff7e

H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 -m pytest src/brain/tests/test_work_navigation_sdk.py src/brain/tests/test_work_navigation_transport.py -q -p no:cacheprovider -p ultima_nav_pathcheck --basetemp=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c1-green\temp --junitxml=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c1-green\junit.xml

135 passed in 35.03s

{"invocation.json": "c3942f479c9fca711b0123966680fd04bf899f2fecadd6a49adaf13ce5f8c5ad", "junit.xml": "856531ba1078ab451aa85dc9b8647168c53867569e09c397a05a9244e7ae1d9a", "loaded-paths.json": "0b113cd8edff2b19630480c1abcb12981d43aedfaff9b665cc1b298c5e79ae6b", "stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stdout.log": "dc74673f2574168b72d69dd509a268435cceac854e8a53fca86cc05070e1d0b0", "ultima_nav_pathcheck.py": "88adfb44f6a64ef460a31586178204ffba0925e956e30934132a9a0bf2263548"}

### c2-red

Receipt H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c2-red\receipt.json SHA-256 31f62d88266ff523cb69091c86b8127e78def867fa6bc414e6e4cd64b25ae9e2

H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 -m pytest src/brain/tests/test_work_navigation_transport.py::test_v3_provisional_third_card_no_promotion_on_failure[blank_final] -q -p no:cacheprovider -p ultima_nav_pathcheck --basetemp=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c2-red\temp --junitxml=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c2-red\junit.xml

1 failed in 2.69s

{"invocation.json": "14f71865a91a1db100710ae3d4b29b1677c1b0eb509f0571f4e5b4f18334693a", "junit.xml": "81a27c40de7033ad97ff14fc90dd58dba79caeda65c059cde8b7886bf9d544ad", "loaded-paths.json": "bbb9fd85463308337e23b367b8243538828647cf946402d6c030a8be226cbe77", "stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stdout.log": "50c4bbfddec6834f1bee5d57af52686959b7ff5849bfe8bbc40d13d73fa0ae8a", "ultima_nav_pathcheck.py": "88adfb44f6a64ef460a31586178204ffba0925e956e30934132a9a0bf2263548"}

### c2-green

Receipt H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c2-green\receipt.json SHA-256 8b8f2bd9ad83ecb34d0c29780c95925e8fd58eb8ebde08e280773cd924ef1fc6

H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 -m pytest src/brain/tests/test_work_navigation_sdk.py src/brain/tests/test_work_navigation_transport.py -q -p no:cacheprovider -p ultima_nav_pathcheck --basetemp=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c2-green\temp --junitxml=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-c2-green\junit.xml

136 passed in 35.94s

{"invocation.json": "946ed0cfb293a8e46cda4bb4564a011ecabec6d3e647db00842666a39fda689c", "junit.xml": "51201225baae2507d5706ef3adbfcb2c0ffa47f27cf19dc8c1218d8a6e1c95c6", "loaded-paths.json": "791e61363bf923c47e2d25e2e6f098f392e752591f4b4e693eab34fbdf512489", "stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stdout.log": "0511608c8696ba16bdee307fbcf3fe3ced1ec7c550c552d80a433dfeed993b10", "ultima_nav_pathcheck.py": "88adfb44f6a64ef460a31586178204ffba0925e956e30934132a9a0bf2263548"}

### covering

Receipt H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\receipt.json SHA-256 d12f6bd062966fce907260878e4656072ee1ea7e6b8178602febce30098da779

H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 -m pytest src/brain/tests/test_work_research.py src/brain/tests/test_work_context.py src/brain/tests/test_work_delivery.py src/brain/tests/test_agent_server_sse.py src/brain/browser/tests/test_browser_channel_s3.py src/brain/tests/test_interaction.py src/brain/tests/test_work_navigation.py src/brain/tests/test_work_navigation_sdk.py src/brain/tests/test_work_navigation_transport.py -q -p no:cacheprovider -p ultima_nav_pathcheck --basetemp=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\temp --junitxml=H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\junit.xml

479 passed in 90.25s (0:01:30)

{"invocation.json": "ef1725d4fc0da3f5dd2429d7496787ea783d9309620efb453c3ee18c98f66097", "junit.xml": "09b02d1430d4e87654ded7d9d778ed58aa6a2ac087761642916217f4e2800134", "loaded-paths.json": "5539b4f15d2d49f12e2e5b29f8877dc73ca0ae9c8822ad60ea6a258888c20a36", "stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "stdout.log": "634c43a0c5228e66cdf98dba34a6dcfe2a78b0cae6a07de7de37579030d0cc29", "ultima_nav_pathcheck.py": "88adfb44f6a64ef460a31586178204ffba0925e956e30934132a9a0bf2263548"}

### compat

Receipt H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-compat\receipt.json SHA-256 58e6b5c5ca71934effacddf30cd808ea92ec4729f561a9036a1048bee717c8a0

H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -B -X utf8 H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-compat\run_compat.py

8 passed, 1 warning in 0.13s

{"compat-loaded-paths.json": "3122d8c8ad1508931d83dd127ed2b1c1c3ac82b4056b4fdaf1467b69d5fd80ec", "compat.xml": "6b52953a4c0bfce7e3f7223fa426179c1fb57d568302edd150de0b772fcf3761", "invocation.json": "3325373b0e8b31aff59189e29195f3010dd295b4ec1f05bddfe6a714d6108465", "run_compat.py": "4f59ea751d1ffee40e32979a49043c075561697d8e06250f5579281ee906e66a", "stderr.log": "3b8872274710d547f22a3af7745f6e2e6f255c09a45bd3680e32721275ed60dd", "stdout.log": "e4abe79cc024179fb794af0a05f6bb66d8c2b31c5d613ab83ce05156c1dc8c80"}

All 475 prior suite-qualified identities and the 65 original research purposes and exact source bytes are retained. All eight compatibility IDs are retained. Compatibility logged one anyio pytest assertion-rewrite warning. The full suite and compatibility suite each ran once on final bytes. Neither final suite skipped or xfailed any case.

## External readback

- text — 337 bytes at H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\temp\test_v3_native_react_observati0\00000000-0000-0000-0000-0000000007d0\research.md, SHA-256 manifest 0b0040545ae70c219623976a27f172a975e22c344042f9e2b794d41efcf9b92b. {"artifact_sha256": "99c40cc2a82443f25b94d923d365b32b9f562ba53d6b07411f762faf5cf621cc", "inputs_sha256": "f37863bad17295d587a6267158534eed283f6a30f557d3a1af9d148613da9014", "issued_sha256": "994dcff83632909ffa2864ba47e2ee48bf9f62b9824d5c8d45db3761c0385937", "prewrite_sha256": "d997c7e2daace546e67af8e1c43f0771615fc39bd69be4b92c02db0137b2ffea", "runtime_sha256": "83bccc3d2cbeeec886d36f9957935b9a01d21b20754d3916479562c5332bdb5b", "views_sha256": "8d530a32549595da92a2380e021a769dbbb829dacf2c6f75cf9ea535ea473615"}
- permuted — 337 bytes at H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\temp\test_v3_native_react_observati1\00000000-0000-0000-0000-000000000bb8\research.md, SHA-256 manifest 6b9773baf11148efa78f203e26328c1094d279310462a77df44fcad6249628b3. {"artifact_sha256": "dd354073e02fae32cd56ec4a675392e44c2b093707e18c9346e809650b072163", "inputs_sha256": "af66b5c714ff4354b68c230f9c1375203eefc3ce80ffc5c1b5bb962f9535d6c9", "issued_sha256": "589bfef0f90b5eae7546dc5bd1e86e1883969129f8a7afd9689c1aaf697bb2b9", "prewrite_sha256": "8a8f7c6514875d495cb7463301ae69757a8178e620940fb231ee78f45692ecfa", "runtime_sha256": "1d6775d238943a6c032110f6987726a117657463d0916dbb64160e1450a3f2f4", "views_sha256": "44dedb4dc622b06bdb9fa45b3281091dbeaa2a5f032cb1ba8560e9770cb6d2b6"}
- html — 370 bytes at H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\temp\test_v3_native_react_observati2\00000000-0000-0000-0000-000000000fa0\research.md, SHA-256 manifest b6e006c1af6271479af7be20f441dda06b570f2c3e4618621c5534dc58feee7c. {"artifact_sha256": "3b299a15eab3e1b3cff171aa62adddb7507e5adea5f205eacc2790be7dca7fb3", "inputs_sha256": "e9713844352adeb49c246144f279ed4235b468e864410608a506f8ea47256b8b", "issued_sha256": "7b1303c128a8dfc148455180e3ce8464ae7711563c1453bfba914101a14a0a3c", "prewrite_sha256": "06ef12c2977757657e45dccd9c0595b552241a96ebbd04a6b7b5ddb7682843c2", "runtime_sha256": "8487cc34541113afbc05eb3f7d4f6acf5f7823e3215051651368d3bd06b8a72b", "views_sha256": "826779ca81e8a3e3bf5a9c640477166420af762687503b6ae14d7ef91a276d15"}
- mixed — 341 bytes at H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-covering\temp\test_v3_native_react_observati3\00000000-0000-0000-0000-000000001388\research.md, SHA-256 manifest 280564f2b18b079f27ef578209c1ead6a1a3e003fba4ce16192bbc3640f7a58c. {"artifact_sha256": "ffe81b973dce3a48e12b79bfa3728d8c3d1a101a3c40889faaf67ea42fc26057", "inputs_sha256": "b5e65d95a197bedacc9a296672b483d30de7781ac0a50268b01a055145210d6b", "issued_sha256": "45be5d288f1c76817b90cbf4d7fbe7be8d5d9db6588c8a24a66b4925e6c1c3a9", "prewrite_sha256": "fff05eecdf2a0b2f70f64d66d7afa25df877315369100603fe757affa25296ca", "runtime_sha256": "bf056e10cadf5d44ce97c926edb99e3a231393979a9bd53815565c48bf28d013", "views_sha256": "c71e7e42b49a1fd8fdf1f38bb4c8d46d0e2ca303331eeb448749256da95d7802"}

The separate stdlib fractional oracle reopened six captures and 90 prepared HTTPX request records against the final inputs, checked binary64 caps, ordering, staged and final replay and reopened file hashes. Positive and fractional readbacks ran after pytest exited.

- H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-readback\verify_external.py SHA-256 aae2c6d4a2d39e980110ea51406e4c9ad9bd5bb17067038cd16f4724c5db50b1
- H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-readback\external-verification.json SHA-256 25d636652b60d90c01046473eb0ba9763075952acfb89d57d592a6777189754b
- H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-readback\verify_fractional.py SHA-256 50cfd6999c1d01c943ce128916661481b1fdf32a13f29f952ef6186d22a56e86
- H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-readback\fractional-verification.json SHA-256 0250e59ee4df09b3e744d11efd1d6b4de063378e9a430b1d33ba3fa090c408e7
- H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-readback\readback.json SHA-256 d1da5ba1e17c3a80aeb19095183ccf778773c25a76db5dc2750f2bf08b7a48c5
- H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-readback\staged-check.json SHA-256 f4ff104b1dd07648230d2131ae6b55ebfd1b42e1bf7cf2099ff0c1510b9b788a
- H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\candidate-fixwave1-readback\post-commit.json SHA-256 5880ed90cf1e336c5ec71de8679e0594da2b1f8210307abba287fc01e16ee564

## Commit and scope

All 31 final inputs match before/after/current, all 30 tracked inputs match HEAD blobs, and src/brain/browser/tests/test_browser_channel_s3.py remains byte-bound and untracked. All 22 installed SDK sources, frozen five, approved design, plan, protocol, prior report and review inputs were rehashed. Exact scoped diff and whitespace checks passed. Changed Git blob SHA-256 values:

{
  "src/brain/agent_server.py": "ffdef7cc5846596364c0e258b7d9c5c8bb3c91d086e50bfd28acdaddc2acfa68",
  "src/brain/tests/test_work_navigation_transport.py": "ff52a0c5f0f5b5753fa91c7ddaf782417dfd28250d491708b8a89756174ff804",
  "src/brain/work_service.py": "d56e0004531ad7f14d51e4d01c3e65cd5b1f5dded90accd18f4d28be9ea5a56f"
}

The code wave is ready for the original whole-candidate reviewer’s scoped rereview. Mechanical scripted SDK and transport proofs do not establish model factual quality, original-corpus acceptance, real-network success or production readiness. Task 4, real 8B execution, T2 acceptance, T3 and release remain pending. No harness, model endpoint, product default, dependency, scanner, SDK, queue, process, UI or audio changes. E02/T2 NOT_PASSED.
