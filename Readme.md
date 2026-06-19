# Run your Julia test cases with JuliaTesting

This plugin defines a command to run Julia test cases, and display the outcome in a Terminus tab. A key binding is provided, imitating that of Visual Studio Code.
At the moment, this plugin imposes the following requirements:

1. The set of all test cases is accessible from `test/runtests.jl` relative to the project directory
2. There is a project `test` defined in `Project.toml`
3. JETLS `testrunner` is installed

Points 1 and 2 are just good practices and I don't intend to deviate from them. Point 3 is motivated by the features brought by `testrunner`. You can read about them [here](https://aviatesk.github.io/JETLS.jl/release/testrunner/). The discussion is focused on Visual Studio Code but the concepts apply to Sublime Text too.
