Route Mapper
---

A pentest tool aimed at making source code assisted C# testing a little better.

**Problem Statement**
> I got given a C# code base and the webapp doesn't expose Swagger info and the code base doesn't build. What routes exist with what auth, and are any juicy?

---

*Yes, I got nerd snipped into making a proper tool instead of using string manipulation + Regex.*

### Usage

At this stage it only exposes the raw AST extracted data and does no extrapolation. Future releases will provide this functionality but for now here is a use case example.

`pip install route-mapper` or `uv add route-mapper`

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
    "routes": [
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