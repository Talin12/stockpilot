variable "project" {
  description = "Name prefix for every resource."
  type        = string
  default     = "stockpilot"
}

variable "environment" {
  description = "Environment label added to all resources as a tag."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "stockpilot-eks"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Versions past standard support are billed at the (6x) extended-support rate."
  type        = string
  default     = "1.35"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones (one public + one private subnet in each)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "EKS needs subnets in at least two AZs; use 2 or 3."
  }
}

variable "node_instance_types" {
  description = "Instance types for the managed node group. m7i-flex.large (2 vCPU, 8 GiB) is allowed on AWS Free-plan accounts, which reject t3.medium."
  type        = list(string)
  default     = ["m7i-flex.large"]
}

variable "node_capacity_type" {
  description = "ON_DEMAND, or SPOT for roughly 60-70% cheaper (but interruptible) nodes."
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_capacity_type)
    error_message = "node_capacity_type must be ON_DEMAND or SPOT."
  }
}

variable "node_min_size" {
  description = "Minimum worker nodes."
  type        = number
  default     = 2
}

variable "node_desired_size" {
  description = "Desired worker nodes. 2 x m7i-flex.large fits the app, Traefik and kube-prometheus-stack, and stays within the 5-vCPU quota of new accounts."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum worker nodes (raise it if your account's On-Demand vCPU quota allows)."
  type        = number
  default     = 2
}

variable "cluster_admin_arns" {
  description = "Extra IAM principal ARNs (e.g. the CI/CD deploy user) granted cluster-admin through EKS access entries."
  type        = list(string)
  default     = []
}
