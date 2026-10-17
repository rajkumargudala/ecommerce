# GitHub Actions security setup

The workflow uses GitHub's OIDC federation for short-lived AWS credentials. It only requests AWS credentials on pushes to `main` and `version-1.0.4`; pull requests and manual runs build and scan images without publishing them.

## AWS OIDC role

In AWS IAM, create the GitHub identity provider with:

- Provider URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`

Create a role for GitHub Actions with a trust policy restricted to this repository and the two publishing branches. Replace the account ID in the federated provider ARN.

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
            "repo:rajkumargudala/ecommerce:ref:refs/heads/main",
            "repo:rajkumargudala/ecommerce:ref:refs/heads/version-1.0.4"
          ]
        }
      }
    }
  ]
}
```

If this repository uses GitHub's immutable OIDC subject claims, use the repository's actual `sub` values from the GitHub OIDC settings in place of the two subject strings above. Keep the audience and branch restrictions.

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

Create a GitHub Actions environment named `production`, restrict its deployment branches to `main`, and require one or more reviewers. The workflow waits on that environment before it opens a GitOps promotion pull request.

Protect `main` and `version-1.0.4` in the source repository. Require pull requests and the `CI gate` status check before merging. The `CI gate` includes Helm validation, SonarQube when secrets are available, Trivy scans, and every image build and scan. Fork and Dependabot pull requests cannot receive `SONAR_TOKEN`, so their SonarQube analysis is skipped.

Protect `main` in the GitOps repository and require its normal review and deployment checks. CI maintains one automation branch and pull request for image promotion; it does not push image updates directly to the deployment branch.
