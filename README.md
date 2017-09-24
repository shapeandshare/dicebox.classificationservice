Classification Service
===============
Provides an end-point that performs classifications via REST API calls.

Overview
--------
  A REST API that performs classification using the designated network structure and weights.
  
**Start the service (development only):**
```
    python ./classificationservice.py
```

I've tested running dicebox with uwsgi, and proxied through nginx.  Nginx configurations can be found within ./nginx of this repository.
```
uwsgi --http-socket 127.0.0.1:5000 --manage-script-name --mount /=classificationservice.py --plugin python,http --enable-threads --callable app —master
```

### Production Deployment

**Docker Container**

The recommended way to run the service is by using the official provided docker container.
The container should be deployed to a Docker Swarm as a service.

**Example**
```
docker service create \
--detach=false \
--publish 8003:80 \
--replicas 0  \
--log-driver json-file \
--name classificationservice shapeandshare/dicebox.classificationservice
```

How to apply rolling updates of the service within the swarm:
```
docker service update --image shapeandshare/dicebox.classificationservice:latest classificationservice
```

In the examples above the Docker Swarm was deployed to AWS and had the Cloudstor:aws plugin enabled and active.
The classification service containers will store and read data from the shared storage.

**Global shared Cloudstor volumes mounted by all tasks in a swarm service.**

The below command is an example of how to create the shared volume within the docker swarm:
```
docker volume create -d "cloudstor:aws" --opt backing=shared dicebox
```

Classification Service API
===========

Default URL for API: `http(s)://{hostname}:5000/`


### Anonymous End-Points


* **Get Service API Version**

For verification of service API version.

```
    [GET] /api/version
```

Result:
`
{
    "version": "String"
}
`

* **Get Service Health**
 
For use in load balanced environments.

```
    [GET] /health/plain
```
Result:
`true` or `false` with a `201` status code.


### Authentication Required End-Points


**Request Header**

The below end-points require several headers to be present on the request.

```
    'Content-type': 'application/json',
    'API-ACCESS-KEY': 'String',
    'API-VERSION': 'String'
```

* API-ACCESS-KEY: 'A unique (secret) guid used for authorization'
* API-VERSION: 'Version of the API to use'

* **Classification**

Used to classify the image data.  Return the label index for the classification.


```
    [POST] /api/classify
```
Post Body: `{ "data": "Base64 encoded PNG image" }`

Result: `{ "classification": integer }`


Example
```
    {
        "classification": 7
    }

```
* **Get Categories**

 Used to turn classification results into human-readable labels.

```
    [GET] /api/categories
```
Result: A list of label to index mappings.

Example

```
    {
        "category_map": {
            "0": "1d4_1",
            "1": "1d4_2",
            "2": "1d4_3",
            "3": "1d4_4",
            "4": "1d6_1",
            "5": "1d6_2",
            "6": "1d6_3",
            "7": "1d6_4",
            "8": "1d6_5",
            "9": "1d6_6",
            "10": "unknown"
        }
    }
```


Contributing
------------
1. Fork the repository on Github
2. Create a named feature branch (like `add_component_x`)
3. Write your change
4. Write tests for your change (if applicable)
5. Run the tests, ensuring they all pass
6. Submit a Pull Request using Github

License and Authors
-------------------
MIT License

Copyright (c) 2017 Joshua C. Burt

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.