terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- Networking: public/private subnet separation ---
resource "aws_vpc" "helpdeskx" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "helpdeskx-vpc" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.helpdeskx.id
  cidr_block              = cidrsubnet(aws_vpc.helpdeskx.cidr_block, 8, count.index)
  map_public_ip_on_launch = true
  availability_zone       = var.availability_zones[count.index]
  tags = { Name = "helpdeskx-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.helpdeskx.id
  cidr_block        = cidrsubnet(aws_vpc.helpdeskx.cidr_block, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]
  tags = { Name = "helpdeskx-private-${count.index}" }
}

# --- Managed Kubernetes cluster ---
resource "aws_eks_cluster" "helpdeskx" {
  name     = "helpdeskx-cluster"
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
  }
}

resource "aws_eks_node_group" "helpdeskx_nodes" {
  cluster_name    = aws_eks_cluster.helpdeskx.name
  node_group_name = "helpdeskx-workers"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  scaling_config {
    desired_size = 2
    max_size     = 6
    min_size     = 2
  }
}

# --- Managed Postgres ---
resource "aws_db_instance" "helpdeskx_db" {
  identifier             = "helpdeskx-db"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "helpdeskx"
  username               = "helpdeskx"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.helpdeskx.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot    = true
}

resource "aws_db_subnet_group" "helpdeskx" {
  name       = "helpdeskx-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "db" {
  name   = "helpdeskx-db-sg"
  vpc_id = aws_vpc.helpdeskx.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.helpdeskx.cidr_block]
  }
}

# IAM roles omitted here for brevity — see iam.tf in a full deployment.
