#lang racket
(require racket/date "library/catalog.rkt")
(provide run-secretary)

(define INPUT_DIR (getenv "SECRETARY_INPUT_DIR"))
(cond ((false? INPUT_DIR) (error "Need to set SECRETARY_INPUT_DIR"))
      ((not (directory-exists? INPUT_DIR)) (make-directory INPUT_DIR)))
(printf "Secretary monitoring ~a\n" INPUT_DIR)

(define (creation-datetime file)
   (parameterize ((date-display-format 'iso-8601)) 
		 (date->string (seconds->date (file-or-directory-modify-seconds file)) #t)))

(define (add-file-to-catalog cat filename)
  (let ((file (build-path INPUT_DIR filename)))
    (printf "Adding ~a to catalog\n" file)
    (add-to-catalog #:catalog           cat 
		    #:name              (path->string filename) 
		    #:creation-datetime (creation-datetime file)
		    #:contents          (file->bytes file))
    (delete-file file)))

(define cat (make-catalog (getenv "CATALOG_FILE")))

(define (run-secretary)
  (displayln "Secretary running")
  (for-each ((curry add-file-to-catalog) cat) (directory-list INPUT_DIR))
  (sleep 1)
  (run-secretary))