# GitHub Actions -> AWS without stored secrets.
# The workflow requests a short-lived OIDC token from GitHub, and AWS STS exchanges it for
# temporary credentials of this role. Only the main branch / production environment of
# var.github_repository can assume it.

variable "github_repository" {
  description = "GitHub repository (owner/name) allowed to deploy."
  type        = string
  default     = "Talin12/stockpilot"
}

variable "github_oidc_subject_prefixes" {
  description = <<-EOT
    Subject-claim prefixes GitHub puts in this repository's OIDC tokens. Read yours with
      gh api repos/<owner>/<repo>/actions/oidc/customization/sub -q .sub_claim_prefix
    Newer repositories use immutable IDs (repo:Owner@<owner-id>/repo@<repo-id>), so a deleted and
    re-created repository with the same name cannot assume the role. Older ones use repo:Owner/repo.
  EOT
  type        = list(string)
  default     = ["repo:Talin12@186754467/stockpilot@1420236630"]
}

variable "create_github_oidc_provider" {
  description = "Create the account-wide GitHub OIDC provider. Set false if the account already has one."
  type        = bool
  default     = true
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc_provider ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc_provider ? 0 : 1
  url   = "https://token.actions.githubusercontent.com"
}

locals {
  github_oidc_provider_arn = var.create_github_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.github[0].arn
}

data "aws_iam_policy_document" "github_deploy_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.github_oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # A job that uses `environment: production` presents the environment claim instead of the ref.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values = flatten([
        for prefix in var.github_oidc_subject_prefixes : [
          "${prefix}:ref:refs/heads/main",
          "${prefix}:environment:production",
        ]
      ])
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  name                 = "${var.cluster_name}-github-deploy"
  description          = "Assumed by GitHub Actions (${var.github_repository}) to deploy with Helm"
  assume_role_policy   = data.aws_iam_policy_document.github_deploy_assume.json
  max_session_duration = 3600
}

# AWS-side permission is only what `aws eks update-kubeconfig` needs; what the role may do
# inside the cluster is granted separately through the EKS access entry in eks.tf.
data "aws_iam_policy_document" "github_deploy" {
  statement {
    actions   = ["eks:DescribeCluster"]
    resources = [module.eks.cluster_arn]
  }
}

resource "aws_iam_role_policy" "github_deploy" {
  name   = "eks-describe"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_deploy.json
}

output "github_actions_role_arn" {
  description = "Set as the AWS_DEPLOY_ROLE_ARN repository variable in GitHub."
  value       = aws_iam_role.github_deploy.arn
}
