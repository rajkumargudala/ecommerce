# GitHub Actions security setup

The workflow uses GitHub's OIDC federation for short-lived AWS credentials. It only requests AWS credentials on pushes to `main` and `version-1.0.4`; pull requests and manual runs build and scan images without publishing them.

## AWS OIDC role

In AWS IAM, create the GitHub identity provider with:

- Provider URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`

Create the `github-actions-ecommerce-ecr-publish` role with a trust policy restricted to this repository and the two publishing branches. This repository uses GitHub's immutable OIDC subject format, which includes its owner and repository IDs. Replace the account ID in the federated provider ARN.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": [
            "repo:rajkumargudala@191754930/ecommerce@1414337297:ref:refs/heads/main",
            "repo:rajkumargudala@191754930/ecommerce@1414337297:ref:refs/heads/version-1.0.4"
          ]
        }
      }
    }
  ]
}
```

Keep the `aud` condition and both branch restrictions when configuring the role.

Attach a role policy that allows ECR login and push only to the `ecommerce-platform` repository. Replace `<AWS_ACCOUNT_ID>` as needed.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart"
      ],
      "Resource": "arn:aws:ecr:us-east-1:<AWS_ACCOUNT_ID>:repository/ecommerce-platform"
    }
  ]
}
```

Add the role ARN as the `AWS_ROLE_ARN` Actions repository variable. Once the workflow has successfully published an image, remove `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` Actions secrets if they were previously configured for this pipeline.

## GitHub repository settings

Add these Actions variables and secrets:

| Name | Type | Purpose |
| --- | --- | --- |
| `AWS_ROLE_ARN` | Variable | IAM role above; used for ECR publishing via OIDC |
| `SONAR_HOST_URL` | Variable | SonarQube Server URL |
| `SONAR_TOKEN` | Secret | Token that can analyze both configured SonarQube projects |
| `GITOPS_TOKEN` | Secret | Fine-grained token for `rajkumargudala/ecommerce-gitops` with Contents read/write and Pull requests read/write |

Create two GitHub Actions environments for the promotion job:

- `production`: restrict deployment branches to `main` and require one or more reviewers.
- `release`: restrict deployment branches to `version-1.0.4`. Add reviewers if release promotions should wait for approval.

The workflow uses `production` for pushes to `main` and `release` for pushes to `version-1.0.4`. It opens the corresponding GitOps pull request only after image publishing and all CI gates succeed.

Protect `main` and `version-1.0.4` in the source repository. Require pull requests and the `CI gate` status check before merging. The `CI gate` includes Helm validation, SonarQube when secrets are available, Trivy scans, and every image build and scan. Fork and Dependabot pull requests cannot receive `SONAR_TOKEN`, so their SonarQube analysis is skipped.

Protect `main` and `gitops-release-1.0.4` in the GitOps repository and require their normal review and deployment checks. CI maintains a separate automation branch and pull request for each source branch. Each pull request updates image tags and copies the frontend Deployment and Service templates from the matching source commit, while preserving the GitOps `values.yaml` and its other workload-specific templates. CI does not push these changes directly to deployment branches.
