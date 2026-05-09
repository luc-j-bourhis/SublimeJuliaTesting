# Run your Julia test cases with JuliaTesting

This plugin defines a handful of commands to run Julia test cases, and display the outcome in a Terminus tab. Key bindings are provided for each command, imitating those in Visual Studio Code.
At the moment, this plugin imposes the following requirements:
1 tests can be run by including `test/runtests.jl`
2 there is a project `test` defined in `Project.toml`
3 `test/runtests.jl` is written as follow
```
module AllTests
...
using ReTest
...
@testset "Something" begin
    ...
    @test ...
    ...
end
...
end

using .AllTests
if isempty(ARGS)
    AllTests.retest()
else
    AllTests.retest(ARGS)
end
```

Assumptions (1) and (2) are just good practice and I do not plan to lift them. As for (3), the rationale is that `ReTest` is the only testing framework which provides an easy way to selectively run a subset of the tests (at least to my knowledge, and at the time of writing). Without that feature, the commands `julia_run_chosen_tests` and `julia_run_last_tests` would not work. Until other packages provide an easy way to select tests based on substrings in their names, I do not plan to lift the requirement that ReTest is used by the Julia package.
