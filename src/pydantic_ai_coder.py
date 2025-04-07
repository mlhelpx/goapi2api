from __future__ import annotations as _annotations

from dotenv import load_dotenv
import logfire
import asyncio
import os
import sys
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Add the parent directory to sys.path to allow importing from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

provider = os.getenv('LLM_PROVIDER') or 'OpenAI'
llm = os.getenv('PRIMARY_MODEL') or 'gpt-4o-mini'
api_key = os.getenv('LLM_API_KEY') or 'no-llm-api-key-provided'

model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

system_prompt = """
I need to implement a Go wrapper for an external API. The wrapper should follow our existing backend structure and coding patterns. Here's an example for the Replicate API:
[example api call]
```shell
curl -s -X POST \
  -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Prefer: wait" \
  -d $'{
    "version": "6ed1ce77cdc8db65550e76d5ab82556d0cb31ac8ab3c4947b168a0bda7b962e4",
    "input": {
      "seed": -1,
      "width": 1024,
      "height": 1024,
      "prompt": "a tiny astronaut hatching from an egg on the moon",
      "output_format": "jpg",
      "guidance_scale": 4.5,
      "output_quality": 80,
      "inference_steps": 2,
      "intermediate_timesteps": 1.3
    }
  }' \
  https://api.replicate.com/v1/predictions
```

I need you to generate all the necessary files for implementing this API wrapper, following our backend structure and patterns. The implementation should:

    Create a database entry to track the job status
    Process the API request asynchronously
    Return a job ID immediately
    Update the job status when the API call completes
    Provide an endpoint to check job status

Here's our file structure and code patterns:

Constants File (constants.go)
        Define model name and status constants
        Example:
```
const (
    API_MODEL_NAME = "API Service Name"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED  = "FAILED"
    STATUS_PENDING = "PENDING"
)
```

//DTO Files (api_dto.go)
    Define request and response structures
    Use proper JSON tags
    Include database model structure
    Example:

```
type APIRequest struct {
    Field1 string `json:"field1"`
    Field2 int    `json:"field2"`
}

type APIResponse struct {
    ID     string                 `json:"id"`
    Status string                 `json:"status"`
    Data   map[string]interface{} `json:"data"`
}

type VirtualModelJob struct {
    ID        uuid.UUID              `json:"id" gorm:"id"`
    ModelName string                 `json:"model_name" gorm:"model_name"`
    Status    string                 `json:"status" gorm:"default:'PENDING'"`
    Result    map[string]interface{} `json:"result" sql:"type:jsonb,omitempty"`
    CreatedAt time.Time              `json:"created_at" gorm:"created_at"`
    UpdatedAt time.Time              `json:"updated_at" gorm:"updated_at"`
}

func (VirtualModelJob) TableName() string {
    return "deployment.virtual_model_jobs"
}
```

Controller (api_controller.go)
    Handle request validation
    Create a job in the database
    Start processing in a goroutine
    Return job ID immediately
    Example:

```
func (ctrl *JobController) APIHandler(ctx *gin.Context) {
    req := dto.APIRequest{}
    if err := ctx.ShouldBindJSON(&req); err != nil {
        ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    jobID := uuid.New()
    modelName := c.API_MODEL_NAME
    if err := ctrl.JobRepo.CreateJob(jobID, modelName); err != nil {
        ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    go func() {
        var job dto.VirtualModelJob
        job.ID = jobID
        resp, statusCode, err := service.APIService(ctx, req, ctx.GetHeader("x-api-key"))
        if err == nil {
            job.Status = c.STATUS_SUCCESS
            job.Result = map[string]interface{}{"result": resp, "status_code": statusCode}
        } else {
            job.Status = c.STATUS_FAILED
            job.Result = map[string]interface{}{"error": err.Error(), "status_code": statusCode}
        }

        job.UpdatedAt = time.Now()
        if err := ctrl.JobRepo.UpdateJob(job); err != nil {
            return
        }
    }()

    ctx.JSON(http.StatusOK, gin.H{"job_id": jobID})
}
```

Repository (job_repository.go)

    Database operations
    Example:

```
type JobRepository struct {
    DB *gorm.DB
}

func (repo *JobRepository) CreateJob(jobID uuid.UUID, modelName string) (err error) {
    job := dto.VirtualModelJob{ID: jobID, ModelName: modelName, Status: c.STATUS_PENDING}
    if err := repo.DB.Table("deployment.virtual_model_jobs").Create(&job).Error; err != nil {
        return err
    }
    return nil
}

func (repo *JobRepository) UpdateJob(job dto.VirtualModelJob) (err error) {
    if err := repo.DB.Table("deployment.virtual_model_jobs").Updates(&job).Error; err != nil {
        return err
    }
    return nil
}

func (repo *JobRepository) GetJobByID(jobID uuid.UUID) (job dto.VirtualModelJob, err error) {
    if err := repo.DB.Table("deployment.virtual_model_jobs").Where("id = ?", jobID).First(&job).Error; err != nil {
        return dto.VirtualModelJob{}, err
    }
    return
}
```

Service (api_service.go)

    Business logic and API call
    Return result, status code, and error
    Example:

```
func APIService(ctx context.Context, req dto.APIRequest, apiKey string) (interface{}, int, error) {
    const APIURL = "https://api.example.com/endpoint"
    
    // Create the API request
    requestBody, err := json.Marshal(&req)
    if err != nil {
        return nil, http.StatusInternalServerError, err
    }
    
    // Prepare request headers
    requestHeader := map[string]string{
        "Content-Type":  "application/json",
        "Authorization": "Bearer " + apiKey,
    }
    
    // Make API call
    response, statusCode, err := externalService.POSTAPIServiceCall(ctx, APIURL, requestHeader, requestBody)
    if err != nil {
        return nil, statusCode, err
    }
    
    // Parse response
    var apiResp dto.APIResponse
    if err := json.Unmarshal(response, &apiResp); err != nil {
        return nil, http.StatusInternalServerError, err
    }
    
    return apiResp, http.StatusOK, nil
}
```

HTTP Helper (http_helper.go)

    Generic HTTP call function
    Example:

```
func POSTAPIServiceCall(ctx context.Context, url string, header map[string]string, jsonByte []byte) ([]byte, int, error) {
    reader := bytes.NewReader(jsonByte)
    req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, reader)
    if err != nil {
        return nil, http.StatusInternalServerError, err
    }

    for key, val := range header {
        req.Header.Set(key, val)
    }
    
    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return nil, http.StatusServiceUnavailable, err
    }

    defer resp.Body.Close()

    respBody, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, http.StatusInternalServerError, err
    }

    if resp.StatusCode >= 400 {
        type ErrorResponse struct {
            Error string `json:"error"`
        }
        var errorResp ErrorResponse
        if err := json.Unmarshal(respBody, &errorResp); err == nil && errorResp.Error != "" {
            return nil, resp.StatusCode, fmt.Errorf("error in response: %s", errorResp.Error)
        }
        return nil, resp.StatusCode, fmt.Errorf("got error with status code: %v, response: %s", resp.StatusCode, string(respBody))
    }
    
    return respBody, resp.StatusCode, nil
}
```

Router Setup (main.go)

    Add route to server
    Example:

```
router := server.Group("api/v1")
router.POST("/api-endpoint", ctrl.APIHandler)
```

Using the Replicate API example I provided, please implement the complete wrapper following our structure. Make sure to:

    Properly handle all API parameters
    Include appropriate error handling
    Parse the response correctly
    Update the job with success/error information

The implementation should be complete and production-ready.


This prompt provides everything needed to create an API wrapper in Go following the structure you've demonstrated. It gives clear instructions and examples for all the required components, and uses the Replicate API example as a practical reference.
"""

pydantic_ai_coder = Agent(
    model,
    system_prompt=system_prompt,
    retries=2
)


if __name__ == "__main__":
    asyncio.run(main())