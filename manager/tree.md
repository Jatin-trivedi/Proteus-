

## Project File Tree

```markdown
└── 📂 jockey-framework
   ├── 📂 .git
   │  ├── 📂 hooks
   │  │  ├── 📄 applypatch-msg.sample
   │  │  ├── 📄 commit-msg.sample
   │  │  ├── 📄 fsmonitor-watchman.sample
   │  │  ├── 📄 post-update.sample
   │  │  ├── 📄 pre-applypatch.sample
   │  │  ├── 📄 pre-commit.sample
   │  │  ├── 📄 pre-merge-commit.sample
   │  │  ├── 📄 pre-push.sample
   │  │  ├── 📄 pre-rebase.sample
   │  │  ├── 📄 pre-receive.sample
   │  │  ├── 📄 prepare-commit-msg.sample
   │  │  ├── 📄 push-to-checkout.sample
   │  │  ├── 📄 sendemail-validate.sample
   │  │  └── 📄 update.sample
   │  ├── 📂 info
   │  │  └── 📄 exclude
   │  ├── 📂 logs
   │  │  ├── 📂 refs
   │  │  │  ├── 📂 heads
   │  │  │  │  └── 📄 main
   │  │  │  └── 📂 remotes
   │  │  │     └── 📂 origin
   │  │  │        └── 📄 HEAD
   │  │  └── 📄 HEAD
   │  ├── 📂 objects
   │  │  ├── 📂 info
   │  │  └── 📂 pack
   │  │     ├── 📄 pack-2f7455e509f1685a6d203c1a2e2d754c31700f35.idx
   │  │     ├── 📄 pack-2f7455e509f1685a6d203c1a2e2d754c31700f35.pack
   │  │     └── 📄 pack-2f7455e509f1685a6d203c1a2e2d754c31700f35.rev
   │  ├── 📂 refs
   │  │  ├── 📂 heads
   │  │  │  └── 📄 main
   │  │  ├── 📂 remotes
   │  │  │  └── 📂 origin
   │  │  │     └── 📄 HEAD
   │  │  └── 📂 tags
   │  ├── 📄 config
   │  ├── 📄 description
   │  ├── 📄 HEAD
   │  ├── 📄 index
   │  └── 📄 packed-refs
   ├── 📂 compiler
   │  ├── 📂 .cache
   │  │  ├── ⚙️ 1182a0164b386d365973ab966683707d299a78486226c89c487f51440a49a989.json
   │  │  ├── ⚙️ 26cb9d54a4df2b23922f06e3248d087182d774ef22d0d09a88ad85f8089ab1b8.json
   │  │  ├── ⚙️ 2ebdcf01953b71a041d1544ee15c07e2309faf63b3d8ef48bd5af3cc151b3db6.json
   │  │  ├── ⚙️ 7541b5b28d48538e21a0563345341d38e3798a3ea21e095ce012854f979d850f.json
   │  │  ├── ⚙️ aafbd08179c426f9fd3180964744aeabf32b22b1f3e63abe275efe4def25025b.json
   │  │  └── ⚙️ c337785b1c1ae37548b548b0793548759ff9a33e0091b15bdd4eab0676e48716.json
   │  ├── 📂 builtins
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 forensic_functions.py
   │  │  └── 📄 function_signatures.py
   │  ├── 📂 codegen
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 ir_optimizer.py
   │  │  └── 📄 llvm_gen.py
   │  ├── 📂 lexer
   │  │  ├── 📂 __pycache__
   │  │  │  ├── 📄 __init__.cpython-311.pyc
   │  │  │  ├── 📄 tokenizer.cpython-311.pyc
   │  │  │  └── 📄 tokens.cpython-311.pyc
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 tokenizer.py
   │  │  ├── 📄 tokens.py
   │  │  └── 📜 tree.md
   │  ├── 📂 parser
   │  │  ├── 📂 __pycache__
   │  │  │  ├── 📄 __init__.cpython-311.pyc
   │  │  │  └── 📄 parser.cpython-311.pyc
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 grammar.py
   │  │  └── 📄 parser.py
   │  ├── 📂 syntax
   │  │  ├── 📂 __pycache__
   │  │  │  ├── 📄 __init__.cpython-311.pyc
   │  │  │  └── 📄 nodes.cpython-311.pyc
   │  │  ├── 📄 __init__.py
   │  │  └── 📄 nodes.py
   │  ├── 📂 tests
   │  │  ├── 📂 sample_scripts
   │  │  │  ├── 📄 array_test.jky
   │  │  │  ├── 📄 for_test.jky
   │  │  │  ├── 📄 function_test.jky
   │  │  │  ├── 📄 hello.jky
   │  │  │  ├── 📄 if_test.jky
   │  │  │  ├── 📄 invalid.jky
   │  │  │  ├── 📄 network_scan.jky
   │  │  │  ├── 📄 registry_scan.jky
   │  │  │  ├── 📄 sample.jky
   │  │  │  ├── 📄 simple.jky
   │  │  │  ├── 📄 struct_test.jky
   │  │  │  ├── 📄 while_test_simple.jky
   │  │  │  └── 📄 while_test.jky
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 test_lexer.py
   │  │  └── 📄 test_parser.py
   │  ├── 📄 __init__.py
   │  ├── 📄 array_test_runtime.c
   │  ├── 📄 array_test_runtime.o
   │  ├── 📄 array_test.exe
   │  ├── 📄 array_test.ll
   │  ├── 📄 array_test.o
   │  ├── 📄 cache.py
   │  ├── 📄 for_test_runtime.c
   │  ├── 📄 for_test_runtime.o
   │  ├── 📄 for_test.exe
   │  ├── 📄 for_test.ll
   │  ├── 📄 for_test.o
   │  ├── 📄 function_test_runtime.c
   │  ├── 📄 function_test_runtime.o
   │  ├── 📄 function_test.exe
   │  ├── 📄 function_test.ll
   │  ├── 📄 function_test.o
   │  ├── 📄 if_test_runtime.c
   │  ├── 📄 if_test_runtime.o
   │  ├── 📄 if_test.exe
   │  ├── 📄 if_test.ll
   │  ├── 📄 if_test.o
   │  ├── 📄 main.py
   │  ├── 📜 README.md
   │  ├── 📄 requirements.txt
   │  ├── 📄 struct_test_runtime.c
   │  ├── 📄 struct_test_runtime.o
   │  ├── 📄 struct_test.exe
   │  ├── 📄 struct_test.ll
   │  ├── 📄 struct_test.o
   │  ├── 📄 while_test_runtime.c
   │  ├── 📄 while_test_runtime.o
   │  ├── 📄 while_test.exe
   │  ├── 📄 while_test.ll
   │  └── 📄 while_test.o
   ├── 📂 manager
   │  ├── 📂 api
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 agent_routes.py
   │  │  ├── 📄 health_routes.py
   │  │  ├── 📄 result_routes.py
   │  │  └── 📄 script_routes.py
   │  ├── 📂 dashboard
   │  │  ├── 📂 static
   │  │  │  ├── 📄 charts.js
   │  │  │  ├── 📄 dashboard.js
   │  │  │  └── 📄 style.css
   │  │  └── 📂 templates
   │  │     ├── 📄 base.html
   │  │     ├── 📄 index.html
   │  │     ├── 📄 realtime.html
   │  │     ├── 📄 results.html
   │  │     └── 📄 scripts.html
   │  ├── 📂 middleware
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 logging_middleware.py
   │  │  └── 📄 request_id.py
   │  ├── 📂 migrations
   │  │  ├── 📂 versions
   │  │  │  └── 📄 8e1938fc8d1c_initial_schema_with_correct_models.py
   │  │  ├── ⚙️ alembic.ini
   │  │  ├── 📄 env.py
   │  │  ├── 📄 README
   │  │  └── 📄 script.py.mako
   │  ├── 📂 models
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 agent.py
   │  │  ├── 📄 deploy.py
   │  │  ├── 📄 result.py
   │  │  └── 📄 script.py
   │  ├── 📄 .env.example
   │  ├── 📄 .gitignore
   │  ├── 📄 app.py
   │  ├── 📄 config.py
   │  ├── 📄 Dockerfile
   │  ├── 📄 gunicorm.conf.py
   │  ├── 📄 logger.py
   │  ├── 📄 rate_limiter.py
   │  ├── 📄 requirements.txt
   │  └── ⚙️ vercel.json
   ├── 📂 polymorphic-engine
   │  ├── 📂 compiled_output
   │  │  ├── ⚙️ sample_metadata.json
   │  │  └── 📄 sample_obfuscated.py
   │  ├── 📂 src
   │  │  ├── 📄 __init__.py
   │  │  ├── 📄 advanced_flow_obfuscator.py
   │  │  ├── 📄 anti_analysis.py
   │  │  ├── 📄 compiler_integration.py
   │  │  ├── 📄 control_flow_flattener.py
   │  │  ├── 📄 dynamic_api_resolver.py
   │  │  ├── 📄 enhanced_demo.py
   │  │  ├── 📄 hash_generator.py
   │  │  ├── 📄 import_table_obfuscator.py
   │  │  ├── 📄 junk_code_injector.py
   │  │  ├── 📄 obfuscator.py
   │  │  ├── 📄 pe_elf_parser.py
   │  │  ├── 📄 string_obfuscator.py
   │  │  └── 📄 variable_encryption.py
   │  ├── 📂 tests
   │  │  ├── 📄 tesi_1.jky
   │  │  └── 📄 test_obfuscator.py
   │  ├── 📄 demo_compiler_integration.py
   │  ├── 📄 enhanced_demo.py
   │  ├── 📄 integration_demo.py
   │  ├── 📄 requirements.txt
   │  └── 📄 sample.jky
   ├── 📂 tests
   │  └── 📄 benchmark.py
   ├── 📄 .gitignore
   ├── 📄 test_compiler_import.py
   ├── 📄 test_e2e_flow.py
   └── 📄 test_integration_with_manager.py

```