variable "aws_region" {
  default = "us-east-1"
}

variable "availability_zones" {
  default = ["us-east-1a", "us-east-1b"]
}

variable "db_password" {
  description = "Password for the HelpDeskX Postgres instance."
  type        = string
  sensitive   = true
}
