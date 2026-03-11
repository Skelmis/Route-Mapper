Route Mapper
---

A pentest tool aimed at making source code assisted C# testing a little better.

**Problem Statement**
> I got given a C# code base and the webapp doesn't expose Swagger info and the code base doesn't build. What routes exist with what auth, and are any juicy?

---

*Yes, I got nerd snipped into making a proper tool instead of using string manipulation + Regex.*

### Features

1. Reading of C# code via a Concrete Syntax Tree (CST) library. This means we have full access to C# specific context and don't rely on educated guesses or homebrew parsing.
2. Separation of CST, Routing and Rules. This means if you would like to you can read the raw method data, build rules off of our routing implementation or otherwise easily access the data you require.
3. Pre-built rules that provide real world value. The kind of things that result in high value findings within 15 minutes.

### Usage

The example provided below generates an `output` folder which contains two nested folders, `rules` and `controllers`.

The `controllers` folder contains a file per C# Controller found within source code. This provides generic information on routing but may be overwhelming on its own in larger code bases.

To this end the `rules` folder provides a file per rule. Rules provide a description of how to interpret the content as well as the results of the rule itself. These are more useful at a glance and provide the primary recommended starting point.

Install with: `pip install route-mapper` or `uv add route-mapper`

Copy the following file and set `base_path` to the path of where the Controllers folder is located.

```python
import json
from pathlib import Path

from skelmis import route_mapper
from skelmis.route_mapper import rules


def main():
    base_path: Path = Path(
        "/path/to/folder/of/Controllers"
    )
    api_classes: list[route_mapper.transform.APIClass] = []
    output_folder: Path = Path("output")
    controllers_folder = output_folder / "controllers"
    rules_folder = output_folder / "rules"
    controllers_folder.mkdir(parents=True, exist_ok=True)
    rules_folder.mkdir(parents=True, exist_ok=True)

    for file in base_path.rglob("**/*Controller.cs"):
        file_content = file.read_text()
        api_class: route_mapper.ast.APIClass = route_mapper.file_to_api_class(file_content)
        route_class: route_mapper.transform.APIClass = route_mapper.transform_ast_to_routes(
            api_class
        )
        api_classes.append(route_class)
        with open(output_folder / "controllers" / f"{file.name}.json", "w") as f:
            f.write(json.dumps(route_class.as_dict(), indent=4))

    implicit_routes: rules.ImplicitRoutes = rules.get_implicit_routes(*api_classes)
    with open(output_folder / "rules" / f"implicit_routes.json", "w") as f:
        f.write(json.dumps(implicit_routes.as_dict(), indent=4))

    policy_grouped_routes: rules.RoutesPerAuthorisationPolicy = rules.get_routes_group_by_authz(*api_classes)
    with open(output_folder / "rules" / f"policy_grouped_routes.json", "w") as f:
        f.write(json.dumps(policy_grouped_routes.as_dict(), indent=4))

    print("Done")


if __name__ == "__main__":
    main()
```

Once run this will generate the folders mentioned prior. Enjoy!

---


For an example of how to retrieve the raw results from the CST level, please refer to the below script.

```python
import json
from pathlib import Path

from skelmis import route_mapper


def main():
    base_path: Path = Path(
        "/path/to/controllers/folder"
    )
    output_folder: Path = Path("output")
    output_folder.mkdir(parents=True, exist_ok=True)
    for file in base_path.rglob("**/*Controller.cs"):
        file_content = file.read_text()
        api_class: route_mapper.ast.APIClass = route_mapper.file_to_api_class(file_content)
        with open(output_folder / f"{file.name}.json", "w") as f:
            f.write(json.dumps(api_class.as_dict(), indent=4))

    print("Done")


if __name__ == "__main__":
    main()
```

If run on the following example file:
```c#
using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace WebApplication1.Controllers;

[ApiController]
[Route("/api/[controller]")]
public class WeatherForecastController : ControllerBase
{
    private static readonly string[] Summaries = new[]
    {
        "Freezing", "Bracing", "Chilly", "Cool", "Mild", "Warm", "Balmy", "Hot", "Sweltering", "Scorching"
    };

    private readonly ILogger<WeatherForecastController> _logger;

    public WeatherForecastController(ILogger<WeatherForecastController> logger)
    {
        _logger = logger;
    }

    [HttpGet(Name = "GetWeatherForecast"), AllowAnonymous]
    public IEnumerable<WeatherForecast> GetBase()
    {
        return Enumerable.Range(1, 5).Select(index => new WeatherForecast
            {
                Date = DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
                TemperatureC = Random.Shared.Next(-20, 55),
                Summary = Summaries[Random.Shared.Next(Summaries.Length)]
            })
            .ToArray();
    }
    
    [HttpGet]
    [Route("woah")]
    public IEnumerable<WeatherForecast> Get(int? max = 5)
    {
        return Enumerable.Range(1, max).Select(index => new WeatherForecast
            {
                Date = DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
                TemperatureC = Random.Shared.Next(-20, 55),
                Summary = Summaries[Random.Shared.Next(Summaries.Length)]
            })
            .ToArray();
    }    
    [HttpPost]
    [Authorize("ManagementAccess")]
    [Route("woah")]
    public IEnumerable<WeatherForecast> Post([FromBody] int? limit, [FromQuery][Range(1, 10, ErrorMessage = "Expected 1-10")] int page = 5)
    {
        return Enumerable.Range(1, 5).Select(index => new WeatherForecast
            {
                Date = DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
                TemperatureC = Random.Shared.Next(-20, 55),
                Summary = Summaries[Random.Shared.Next(Summaries.Length)]
            })
            .ToArray();
    }
    
    public IEnumerable<WeatherForecast> OopsItsPublic()
    {
        return Enumerable.Range(1, 5).Select(index => new WeatherForecast
            {
                Date = DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
                TemperatureC = Random.Shared.Next(-20, 55),
                Summary = Summaries[Random.Shared.Next(Summaries.Length)]
            })
            .ToArray();
    }
    
    private IEnumerable<WeatherForecast> PrivateMethod()
    {
        return Enumerable.Range(1, 5).Select(index => new WeatherForecast
            {
                Date = DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
                TemperatureC = Random.Shared.Next(-20, 55),
                Summary = Summaries[Random.Shared.Next(Summaries.Length)]
            })
            .ToArray();
    }
}
```

The following file output is generated for at a glance review:
```json
{
    "class_name": "WeatherForecastController",
    "is_public_class": true,
    "attributes": [
        {
            "name": "ApiController",
            "arguments": null
        },
        {
            "name": "Route",
            "arguments": [
                "/api/[controller]"
            ]
        }
    ],
    "methods": [
        {
            "method_name": "GetBase",
            "is_public_method": true,
            "return_type": "IEnumerable<WeatherForecast>",
            "arguments": [],
            "attributes": [
                {
                    "name": "HttpGet",
                    "arguments": [
                        "Name = GetWeatherForecast"
                    ]
                },
                {
                    "name": "AllowAnonymous",
                    "arguments": null
                }
            ]
        },
        {
            "method_name": "Get",
            "is_public_method": true,
            "return_type": "IEnumerable<WeatherForecast>",
            "arguments": [
                {
                    "argument_type": "int",
                    "argument_name": "max",
                    "is_nullable": true,
                    "has_default_argument": true,
                    "argument_default": "5",
                    "attributes": []
                }
            ],
            "attributes": [
                {
                    "name": "HttpGet",
                    "arguments": null
                },
                {
                    "name": "Route",
                    "arguments": [
                        "woah"
                    ]
                }
            ]
        },
        {
            "method_name": "Post",
            "is_public_method": true,
            "return_type": "IEnumerable<WeatherForecast>",
            "arguments": [
                {
                    "argument_type": "int",
                    "argument_name": "limit",
                    "is_nullable": true,
                    "has_default_argument": false,
                    "argument_default": null,
                    "attributes": [
                        {
                            "name": "FromBody",
                            "arguments": null
                        }
                    ]
                },
                {
                    "argument_type": "int",
                    "argument_name": "page",
                    "is_nullable": false,
                    "has_default_argument": true,
                    "argument_default": "5",
                    "attributes": [
                        {
                            "name": "FromQuery",
                            "arguments": null
                        },
                        {
                            "name": "Range",
                            "arguments": [
                                "1",
                                "10",
                                "ErrorMessage = Expected 1-10"
                            ]
                        }
                    ]
                }
            ],
            "attributes": [
                {
                    "name": "HttpPost",
                    "arguments": null
                },
                {
                    "name": "Authorize",
                    "arguments": [
                        "ManagementAccess"
                    ]
                },
                {
                    "name": "Route",
                    "arguments": [
                        "woah"
                    ]
                }
            ]
        },
        {
            "method_name": "OopsItsPublic",
            "is_public_method": true,
            "return_type": "IEnumerable<WeatherForecast>",
            "arguments": [],
            "attributes": []
        },
        {
            "method_name": "PrivateMethod",
            "is_public_method": false,
            "return_type": "IEnumerable<WeatherForecast>",
            "arguments": [],
            "attributes": []
        }
    ]
}
```


---

### Gotchas

- Everything is a string. It's in the source as `1`? Cool, now it's `"1"`. Types are hard and too complicated for this use-case.
- Inheritance is not handled. If your API has parent class functionality, this will not see it. 