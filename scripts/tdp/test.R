## libraries
library(httr)
library(jsonlite)
library(rrapply)

## personal token generated from https://bayer-dev.tetrascience.com/account
## max expiration time is 24h
token <- ""

## helper functions

#' Retrieve data from TDP
#' @param fileId character, fileId
#' @param type character, data type to retrieve, must be one of:
#' * \code{file} retrieve the file
#' * \code{metadata} retrieve file metadata and tags
#' * \code{"info"} get file information 
#' * \code{"versions"} get file versions
#' @return if \code{type = "file"} returns the content of the response, otherwise 
#' returns the response as a pretty printed json string
retrieve_data <- function(fileId, type = c("file", "metadata", "info", "versions")) {
	
	type <- match.arg(type, c("file", "metadata", "info", "versions"))
	
	endpoint <- switch(
			type,
			file = "datalake/retrieve",
			metadata = "datalake/metadata-tags",
			info = sprintf("fileinfo/file/%s", fileId),
			versions = sprintf("fileinfo/file/%s/versions", fileId)
	)
	
	query <- switch(
			type,
			file = list(fileId = fileId, getPresigned = "false"),
			metadata = list(fileId = fileId, type = "s3file"),
			info = list(),
			versions = list()
	)
	
	res <- GET(
			url = paste("https://api.bayer-dev.tetrascience.com/v1", endpoint, sep = "/"),
			query = query,
			add_headers(
					"ts-auth-token" = token,
					"x-org-slug" = "bayer-br-dev"
			),
			content_type("application/octet-stream"),
			accept_json()
	)
	if(status_code(res) != 200L) {
		return(content(res))
	} else {
		if(type == "file") {
			txt <- content(res, as = "text", encoding = "UTF-8")
			return(txt)
		} else {
			parsed <- content(res, as = "parsed", encoding = "UTF-8")
			return(parsed)
		}
	}
}

#' Upload or replace file in TDP 
#' @param filePath character, local file path 
#' @param fileName character, file name of uploaded file in TDP
#' @param sourceType character, source type of uploaded file in TDP
#' @param fileId optional character existing fileId of file to replace 
#' @param meta optional named vector of key-value pairs to upload with the file
#' @param tags optional character vector of tags to upload with the file
#' @param labels optional named vector of name-value pairs to upload with the file
#' @return If unsuccessful, returns the raw content of the response. 
#' If successful, returns the character fileId associated with the uploaded file. 
upload_file <- function(filePath, fileName, sourceType = "unknown", fileId = NULL, meta = NULL, tags = NULL, labels = NULL) {
	
	body <- list(
			file = httr::upload_file(path = filePath),
			filename = fileName,
			sourceType = sourceType
	)
	
	if(!is.null(tags)) {
		stopifnot("'tags' must be a character vector" = is.vector(tags) && is.character(tags))
		body <- c(body, list(tags = toJSON(tags)))
	}
	if(!is.null(meta)) {
		stopifnot("'meta' must be a named vector of key-value pairs" = is.vector(meta) && is.character(meta) && !is.null(names(meta)))
		body <- c(body, list(meta = toJSON(as.list(meta), auto_unbox = TRUE)))
	}
	if(!is.null(labels)) {
		stopifnot("'labels' must be a named vector of name-value pairs" = is.vector(labels) && is.character(labels) && !is.null(names(labels)))
		lst <- lapply(seq_along(labels), \(i) list(name = names(labels)[i], value = labels[[i]]))
		body <- c(body, list(labels = toJSON(lst, auto_unbox = TRUE)))
	}
	if(!is.null(fileId) && nzchar(fileId)) {
		body <- c(body, list(sourceFileId = fileId))
	}
	
	res <- POST(
			url = "https://api.bayer-dev.tetrascience.com/v1/datalake/upload",
			body = body,
			add_headers(
					"ts-auth-token" = token,
					"x-org-slug" = "bayer-br-dev"
			),
			encode = "multipart",
			accept_json()
	)
	
	if(!status_code(res) %in% c(200L, 201L)) {
		return(content(res))
	} else {
		return(content(res, as = "parsed")[["fileId"]])	
	}
	
}

#' Search files by metadata, tags or labels
#' @param search_type character, file attribute to search, must be one of: \code{"meta"},
#' \code{"tags"}, or \code{"labels"}
#' @param search_terms character vector of search terms:
#' * If \code{search_type} is \code{"meta"}: a named vector of metadata key-value pairs
#' * If \code{search_type} is \code{"tags"}: a character vector of tags
#' * If \code{search_type} is \code{"labels"}: a named vector of labels name-value pairs
#' @param nmax integer, maximum number of returned hits, defaults to 100
#' @return If unsuccessful, returns the raw content of the response. 
#' If successful returns a data.frame with columns \code{filePath} and \code{fileId} 
#' of the found files in TDP.
search_files <- function(search_type = c("meta", "tags", "labels"), search_terms, nmax = 100) {
	
	search_type <- match.arg(search_type, c("meta", "tags", "labels"))
	
	if(identical(search_type, "meta")) {
		## TODO: this does not work, metadata labels need to be added to search index first?
		meta <- search_terms
		stopifnot("'meta' must be a named vector of key-value pairs" = is.vector(meta) && is.character(meta) && !is.null(names(meta)))
		terms <- lapply(seq_along(meta), \(i) list(term = setNames(list(meta[[i]]), paste("metadata", names(meta)[i], sep = "."))))
		query <- list(
				bool = list(
						must = list(terms)
				)
		)
	} else if(identical(search_type, "tags")) {
		## TODO: this does not work, tag labels need to be added to search index first?
		tags <- search_terms
		stopifnot("'tags' must be a character vector" = is.vector(tags) && is.character(tags))
		terms <- lapply(tags, \(tag) list(term = list(tags = tag)))
		query <- list(
				bool = list(
						must = list(terms)
				)
		)
	} else if(identical(search_type, "labels")) {
		labels <- search_terms
		stopifnot("'labels' must be a named vector of name-value pairs" = is.vector(labels) && is.character(labels) && !is.null(names(labels)))
		terms <- lapply(seq_along(labels), \(i) list(
							list(term = list("labels.name" = names(labels)[i])), 
							list(term = list("labels.value" = labels[[i]]))
					))
		nested_terms <- lapply(terms, \(term) list(
							"nested" = list(
									path = "labels",
									query = list(
											bool = list(
													must = term
											)
									)
							)))
		query <- list(
				bool  = list(
						must = nested_terms
				)
		)
	}
	
	json_body <- toJSON(
			x = list(
					size = as.integer(nmax),
					"_source" = list(
							includes = c("filePath", "fileId")
					),
					query = query
			),
			pretty = TRUE,
			auto_unbox = TRUE
	)
	
	res <- POST(
			url = "https://api.bayer-dev.tetrascience.com/v1/datalake/searchEql?index=raw",
			body = json_body,
			add_headers(
					"ts-auth-token" = token,
					"x-org-slug" = "bayer-br-dev"
			),
			encode = "raw",
			content_type_json(),
			accept_json()
	)
	
	if(status_code(res) != 200L) {
		return(content(res))
	} else {
		parsed <- fromJSON(content(res, as = "text", encoding = "UTF-8"), simplifyVector = FALSE)		
		hits <- rrapply(
				parsed, 
				condition = \(x, .xname) .xname %in% c("filePath", "fileId"),
				how = "bind",
				options = list(coldepth = 5)
		)
		return(hits)
	}
}


## ----- ##
## Tests ##
## ----- ##

## upload files
fileId1 <- upload_file(
		filePath = "files/CP-TestClonePool_VH_uniques.fasta",
		fileName = "entry/ngs_test_cp_vh_uniques.fasta",
		meta = c("ngs_run_id" = "NGS_RUN001", "ngs_pp_id" = "NGS_PP001"),
		tags = c("NGS", "Clone Pool"),
		labels = c("ngs_run_id" = "NGS_RUN001", "ngs_pp_id" = "NGS_PP001")
)

fileId2 <- upload_file(
		filePath = "files/CP-TestClonePool_VL_uniques.fasta",
		fileName = "entry/ngs_test_cp_vl_uniques.fasta",
		meta = c("ngs_run_id" = "NGS_RUN001", "ngs_pp_id" = "NGS_PP001"),
		tags = c("NGS", "Clone Pool"),
		labels = c("ngs_run_id" = "NGS_RUN001", "ngs_pp_id" = "NGS_PP001")
)

fileId3 <- upload_file(
		filePath = "dummy_scfv12.fasta",
		fileName = "scfv_registration/dummy_sfcv12.fasta",
		sourceType = "sharepoint-online-file",
		labels = c("notebook_id" = "EXP25000345")
)

## search files 
foundFiles <- search_files(
		search_type = "labels", 
		search_terms = c("ngs_run_id" = "NGS_RUN001", "ngs_pp_id" = "NGS_PP001")
)

## retrieve files
info1 <- retrieve_data(foundFiles$fileId[1], type = "info")
file1 <- retrieve_data(foundFiles$fileId[1], type = "file")

info2 <- retrieve_data(foundFiles$fileId[2], type = "info")
file2 <- retrieve_data(foundFiles$fileId[2], type = "file")

## helper function to extract relevant file info
getRelatedFileInfo <- function(raw_info) {
	lapply(raw_info, \(info) {
				list(
						name = basename(info[["filePath"]]),
						path = info[["file"]][["path"]],
						size = list(
								value = round(info[["file"]][["size"]] / 1e3, digits = 1),
								unit = "KB"
						),
						checksum = list(
								value = info[["file"]][["checksum"]],
								algorithm = "unknown"
						),
						pointer = list(
								fileId = info[["fileId"]],
								bucket = info[["file"]][["bucket"]],
								version = info[["file"]][["version"]],
								type = info[["file"]][["type"]],
								fileKey = info[["file"]][["checksum"]]
						)
				)
			})
}

json_info <- getRelatedFileInfo(list(info1, info2))

## prepare dummy json 
json_lst <- list(
		fields = list(
				ngs_run = list(
						name = "NGS_RUN015",
						benchling_registry_id = "NGS_RUN015",
						benchling_api_id = "bfi_4z9qYLIR"
				),
				ngs_pp = list(
						name = "NGS_PP010",
						benchling_registry_id = "NGS_PP010",
						benchling_api_id = "bfi_yKKeqPvo"
				),
				ngs_type = list(
						name = "Clone Pool",
						benchling_schema_id = "assaysch_lKdA5G3j"
				),
				project = list(
						name = "[Bayer] - NGS Pipeline Integration",
						benchling_api_id = "src_drmlF4RB"
				),
				entry = list(
						name = "(WF) Clone pools to NGS [Stelios Test 03.06.2024]",
						benchling_api_id = "etr_GhWFivuQ"
				),
				software = list(
						name = "BiologicsNGS",
						version = "0.29.13"
				),
				sequencer = list(
						name = "Illumina"
				), 
				user = list(
						name = "Stylianos Fodelianakis"
				),
				time = list(
						created = "2025-04-02 14:50:40"
				),
				kumo_s3_file_paths = list(
						list(
								name = "NGS_RUN015/testData_clone_pool_R1.fastq.gz",
								bucket = "kumo-6hs-p5gq8e9ecr1xj4q6hy8nf4bx8nqbkeuc1a-s3alias/dds-ta-raw-ngs"
						),
						list(
								name = "NGS_RUN015/testData_clone_pool_R2.fastq.gz",
								bucket = "kumo-6hs-p5gq8e9ecr1xj4q6hy8nf4bx8nqbkeuc1a-s3alias/dds-ta-raw-ngs"
						)
				),
				related_files = json_info
		)
)

#write_json(json_lst, path = "files/dummy_meta_data.json", auto_unbox = TRUE, pretty = TRUE)

## upload json to TDP
#meta_upload <- upload_file(
#		filePath = "files/dummy_meta_data.json",
#		fileName = "entry/ngs_test_meta.json",
#		meta = c("ngs_run_id" = "NGS_RUN015", "ngs_pp_id" = "NGS_PP010"),
#		tags = c("NGS", "Clone Pool", "Metadata"),
#		labels = c("ngs_run_id" = "NGS_RUN015", "ngs_pp_id" = "NGS_PP010")
#)
#
#file_id <- "ff9a974d-767d-4f03-9c5a-a896f988cea1"

## test API metadata
api_host <- "localhost:8002"
json_data <- jsonlite::read_json(path = "files/dummy_meta_data.json", simplifyVector = FALSE)
json_body <- jsonlite::toJSON(json_data, pretty = TRUE, auto_unbox = TRUE)

query_params <- list(
		labels = toJSON(
				list(
						ngs_run_id = "NGS_RUN015",
						ngs_pp_id = "NGS_PP010",
						ngs_type = "Clone Pool",
						sequencer_type = tools::toTitleCase("illumina")
				),
				auto_unbox = TRUE
		)
)

endpoint <- paste("http:/", api_host, "upload-ts-metadata", sep = "/")

json_upload <- httr::POST(
		url = endpoint,
		body = json_body,
		query = query_params,
		encode = "multipart",
		httr::add_headers(
				"Content-Type" = "application/json"
		),
		httr::verbose()
)

## test API rawfile
file <- httr::upload_file(path = "files/CP-TestClonePool_VH_uniques.fasta")
query_params <- list(
		labels = toJSON(
				list(
						ngs_run_id = "NGS_RUN015",
						ngs_pp_id = "NGS_PP010"
				),
				auto_unbox = TRUE
		)
)
endpoint <- paste("http:/", api_host, "upload-ts-file", sep = "/")

json_upload <- httr::POST(
		url = endpoint,
		body = list(file = file), 
		query = query_params,
		encode = "multipart",
		accept_json(),
		verbose()
)

info <- httr::GET(paste(api_host, "get-ts-fileinfo", "a39f1853-48c1-4994-b6f9-72c3739b676e", sep = "/"))
content(info, as = "parsed")

#file_id <- "68bb1c66-186a-4b25-90d3-5e0fecd6bc98"
#info1 <- retrieve_data(file_id, type = "info")
#file1 <- retrieve_data(file_id, type = "file")

## test API retrieve metadata
pp_id <- "NGS_PP010"
run_id <- "NGS_RUN015"

json_meta <- httr::GET(paste(api_host, "ngs-run-information", run_id, pp_id, sep = "/"))
content(json_meta, as = "parsed")







