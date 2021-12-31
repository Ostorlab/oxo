# Changelog

## Roadmap for November-December-January 2021
**:mag: Detection: improve detection of several vulnerability classes with focus on Flutter and React Native**

- Improve detection of Flutter and React-Native vulnerabilities
- Add detection of several new classes of vulnerabilities
- Improve performance of Dynamic Analysis Instrumentation
- Improve stability of Mobile Device Fleet Infrastructure
- Improve fuzzing of Intents and URL schemes on both Android and iOS with feedback-forward fuzzing
- Improve integration of Log and Backend scanning
- Expose Analysis Environment capabilities with an expression language

**:robot: Integrations: Extend CI/CD integrations**

- Complete Gitlab, Github Actions and Azure DevOps integration

**:bouquet: User Experience: Improve technical detail navigation and feature discovery**

- Expose portions of the Analysis Environment to the community version
- Integrate Analysis Environment with technical detail of several vulnerabilities
- Expose more Secure reported vulnerabilities
- Add Guided Tour to help first-use of the platform
- Improve all notification emails

## September-October 2021

- Release of the Remediation API with better vulnerability lifecycle management, allowing detection of fixed vulnerabilities, re-opens and maintain status of exception and false positives
- New dashboard offering a glass box view into security posture and urgent tasks
- Management of patching and priority policies with SLO and tools to track and measure fix performance
- 3rd Party integrations with Jira
- Add Ticket timeline to with dynamic setting of start and end time
- Add grouping of ticket by status, priority and tag
- Add Ticket bulk edit mode


## August 2021
Focus on improving the Monkey Tester to improve coverage adding support for more strategies and advanced test case
generation. Work also included better handling of Application packaging and management of our fleet of mobile devices.

- :robot: An all improved Monkey Tester with highly improved code coverage
- :bouquet: UI Call coverage visualisation to understand what has been done

## July 2021
Focus on improving Web Scanner detection, adding several features, like Backend fingerprinting, adding more vulnerabilities and
improving Backend Vulnerability representation model. Work also included improving Monkey Tester to support more
advanced testing strategies. Key updates:

- :robot: Adding support for multiple strategies to Monkey Tester
- :beetle: Multiple bug fixes and improvements to Backend Scanner, XSS Scanner, Fingerprint detections
- :robot: Scale search indexing infrastructure to handle the increase in covered assets

## June 2021
- :robot: Support of new backend vulnerabilities, like SQL with JDBC escape sequence, Jinja template injection, Python Object serialisation ...
- :robot: Support of new backend vulnerabilities, like XXE, XSLT injection, Fastjson serialisation,  PHP RCE ...
- :beetle: Tweaks to the JDWP Android monitor for coverage and performance.
- :rocket: Parallelization and backend vulnerability model generation to improve false positive confidence to 6*9 (99.9999%).

## Mai 2021
- :beetle: API traffic improvement and bug fixes
- :mag: Multiple performance and enhanced result for the new search feature
- :robot: New dynamic instrumentation engine for iOS based on LLDB
- :robot: Improve iOS instrumentation to capture SQL, Crypto, Keychain, Zip, Wifi, Webkit, Biometric, Filesystem, HTTP, Preferences dangerous API
- :robot: Enable backtracing of dangerous API to track their usage
- :robot: Support of credential authentication in Web Scan
- :robot: Improved Web Crawling to support mutated html

## April 2021
- :mag: New rules to detect insecure javascript patterns and new insecure secret usage.
- :bouquet: Add search, tagging and call trace of extern functions, like JNI.
- :mag: New scan search capability to search across all analysis asset types.
- :bouquet: API traffic IDE capability.
- :robot: API to persist taint graph from scan.

## March 2021
- :beetle: Fixes to the Analysis Environment indexing to enable code and file search
- :loudspeaker: Deprecate Free+Analysis scan type in a revamp of the analysis environment
- :rocket: Asset inventory model rewrite leading address a performance issues leading to 600% performance improvement of loading scans.
- :robot: Support for persisting taint graph for use by the Analysis Environment and future VulnAPI
- :bouquet: Support for tagging of native function in IDE
- :mag: Add multiple new sinks methods
- :beetle: Remove false positive in detection of RSA/ECB weak encryption
- :beetle: Bug fixes to taint analysis leading missing detections
- :robot: Detection of valid Sendgrid API keys
- :robot: Enhanced detection of dangerous Webview settings and deprecation of non-vulnerable APIs
- :robot: Detection of insecure Zip leading to path traversal arbitrary file overwrite
- :beetle: Fix Twitter API detection


## February 2021
- :loudspeaker: Alpha Release of the Web Scanner
- :rocket: Release of Chrome-powered Crawling
- :robot: Release of Black-box Tree Fuzzer
- :rocket: Release of XSS Detector powered by full-context coverage polyglot payloads
- :robot: Proxy agent persists and collects HTTP requests
- :bouquet: Analysis environment HTTP request and response navigator
- :crystal_ball: Real Time indexing of knowledge Base and Analysis environment for enhanced and fast search
- :beetle: Automated Purge of old community scans
- :mag: Detection of Dependency Confusion


## January 2021
- :robot: Switch API encoding from JSON to UBJSON to add support for binary format
- :bouquet: Analysis Env javascript formatting
- :bouquet: Analysis Env detection of new file formats
- :bouquet: Analysis Env call trace node coloring to match function and method tagging
- :beetle: Multiple bug fixes and performance optimization of the Analysis Env
- :loudspeaker: Support for sharing report access using a shareable link
- :loudspeaker: Add edit mode to vulnerabilities to change risk rating or mark as a false positive
- :rocket: Detection of new secrets keys and dangerous functions

## November, December 2020
- :loudspeaker: Release of Android and iOS application analysis environment
- :rocket: Analysis Env support for APK and IPA file listing with content access
- :rocket: Analysis Env support for Code highlighting for HTML, Javascript, XML, Java, C++
- :rocket: Analysis Env support for Binary plist extraction
- :rocket: Analysis Env support for Macho and ELF file disassembly and decompilation for ARM and ARM64
- :rocket: Analysis Env support for Macho and ELF string listing
- :rocket: Analysis Env support for DEX classes listing
- :rocket: Analysis Env support for DEX smali listing and java decompilation
- :rocket: Analysis Env support for Android resource extraction
- :rocket: Analysis Env support for Android manifest extraction
- :rocket: Analysis Env support for DEX, Macho, and ELF function call trace with full refs and xrefs generation
- :rocket: Analysis Env support for Dangerous functions tagging to identify security hotspots. 
- :rocket: Analysis Env support for Contextual call trace generation.

## October 2020
- :loudspeaker: Release of continuous application monitoring from the store
- :mag: Detection of weak Bluetooth connection
- :mag: Detection of dynamic broadcast receiver with no permissions
- :loudspeaker: New Jenkins Plugin to integrate CI/CD pipelines with Ostorlab (https://github.com/jenkinsci/ostorlab-plugin)
- :bouquet: Email and UI notification to inform of key events (scan completion, password change ...)
- :bouquet: Expose API key generation and management from the UI


## September 2020
- :loudspeaker: Release of Ostorlab lighthouse continuously scanning public applications
- :loudspeaker: Release of Ostorlab VulnDB UI to access internal known vulnz database
- :bouquet: Vulnerability tagged as affecting security and privacy, security only or privacy only
- :mag: Detection of several privacy settings in Android manifest
- :mag: Detection of facebook SDK debug mode
- :mag: Detection of GPS location tracking impacting privacy
- :beetle: Fix insufficient sink default taint and missing propagation for Array and Const 


## August 2020
- :loudspeaker: Store search and scan feature
- :loudspeaker: Deep 3rd party dependencies fingerprinting
- :bouquet: Markdown vulnerability text and description support


## July 2020
- :loudspeaker: Extend 3rd party dependencies rules 
- :rocket: Creation of database of unreported vulnerabilities

## June 2020
- :bouquet: Report libraries and 3rd party dependencies
- :mag: Fingerprinting of Native Android libs, iOS Frameworks, Cordova plugins, Javascript libraries, Xamarin libs and OpenSSL
- :rocket: Vetted and enhanced vulnerability database with all the known vulnerabilities affecting libraries and 3rd party dependencies
- :rocket: Indexing support for Maven Jar and AAR, Cocoapod podspecs and NPM packages
- :mag: Detect calls to dangerous Bluetooth API

## May 2020
- :loudspeaker: Exposure of CVSSv3 score
- :robot: Alpha support for UI Automation rules
- :gift: Add Xamarin decompiled source code to the list of artifacts
- :mag: Detect of secrets (SSH Private Keys, Service Account, Slack Token, etc.)
- :mag: Detect use of deprecated TLS protocols (SSLv2, SSLv3, TLSv1.0, TLSv1.1)

## April 2020
- :bar_chart: Add generation of executive summary PDF report
- :loudspeaker: New `Secure` risk rating to denote secure implementation
- :loudspeaker: New `Hardening` risk rating to differentiate between actual vulnerability and missing hardening mechanism
- :loudspeaker: Add support for archiving scans
- :loudspeaker: Add support for exporting scans
- :mag: Add detection of new sinks and sources leading to insecure file write, insecure TLS and command execution
- :rocket: Enhance performance of taint analysis and increase coverage
- :bouquet: Enhanced representation of taint information
- :bouquet: Enhanced representation of stack traces collected in dynamic analysis
- :warning: Fix inconsistency in risk rating
- :beetle: Fix false positive in iOS detection for missing ARC and Stack Guard protections

## March 2020
- Support for streaming API to create and stops scans
- Subscription support
- New KB entry for Webview LoadURL injection
- Bug fixes to JDWP Hooking engine
- Dashboard update showing scan plan
- Support for stopping and archiving scans

## February 2020
- API for scheduling rules
- Migration to Kubernetes
- Initial support for streaming API to create scans

## January 2020
- API to manage Inventory (mobile apps, urls, domains, ...)
- UI to list, create and update Inventory and Assets
- CI/CD pipeline integration
- Deprecate old UIs

## December 2019 
- Release of the alpha version of the [new reporting front end](https://report.ostorlab.co)
- API naming fixes
- Fix submission of the test credentials
- New Google Play client to support scanning from the Play Store directly
- Several New APIs move to GraphQL (Account and Password Management, Artifcats)
- Worker to handle long-running jobs (PDF generation and Scan Export)

## November 2019
- Progress on the new reporting front end
- Bug fixes in public website
- Simplified pagination support in all APIs
- Experimental API to create Web Scans

## October 2019
- Release of an [open source Android application](https://github.com/Ostorlab/ostorlab_insecureApp) to benchmark vulnerability scanners
- Extensions to the GraphQL API adding support for pagination, vulnerability search and switch from passing applications in Base64 to multi-part support
- Progress on the new reporting front end

## September 2019
- Release of a new documentation website [docs.ostorlab.co](https://docs.ostorlab.co)
- Release of a new website [www.ostorlab.co](https://www.ostorlab.co) using material design

## August 2019
- Major migration of all existing infra and data to the new backends.

## June 2019
- Infra refactoring into a micro-service architecture.
- Separation of user portal and public website to prepare moving to serverless.
- Separation of backend and add an orchestration backend to prepare moving from Swarm to k8s.

## Mai 2019
- Refactoring of API adding support for GraphQL.
- Migration of website, user portal and orchestrator to GraphQL.

## April 2019
- Extending vulnerability test bed.
- Add support for template injection of 4 new Java template engines.
- Add support detection of Ruby code injection.
- Add support detection of Node.js code injection.

## March 2019
- Multiple bug fixes and performance enhancements.
- Fix false positive detection of Template Injection.
- Add support detection of python code injection.
- Add support detection of pickle deserialization injection.

## February 2019
- Multiple bug fixes and performance enhancements.
- Enhance detection of XSS adding support for multiple callbacks vectors.

## January 2019
- New alpha system to detect vulnerabilities in backends from previously collected ones.
- Creation of a new vulnerability test bed.

## December 2018
- Add support for detection of stored XSS.
- Complete rework of the scan authentication module. It works well and sends fewer requests.
- Brand new subscription menu.
- Bug cleaning season.

## November 2018
- Add support for multi-step submitting of Forms.
- Enhancement to automatic detection of CSRF fields and auto-update of CSRF tokens.
- Alpha version of Fingerprinting agents.

## October 2018
- Major enhancement coverage of XSS contexts, long live Polyglot payloads.

## September 2018
- Enhance CSRF handling for web scanning.
- Add scan export and import feature for on-premise scanning support.
- Implementation of ADB Proxy agent for on-premise scanning support.
- Add collection of screenshots and logcat traffic during dynamic analysis.
- New security rules for Android Network Security Configuration.
- Fix false positives in Cryptography rules using static taint.
- Rework of all rules formatting.
- Fix PDF generation and add support for code highlighting.
- Add support for kown pathes crawling
- Add Artifact panel to store extracted source code, screenshots and traffic logs.
- Add Xamarin source code decompilation.
- Fix duplicate request testing by backend and XSS scanner.
- Initial work on CSRF token detection and generation for POST request fuzzing.
- Add support for inserting payloads in sub-pathes.

## August 2018
- Extensive bug fixes month of all core components.
- Enhance testability of the scanning engine.
- Enhance reporting features.

## July 2018
- Enhanced detection of template injection vulnerabilities.
- New scanner for detecting XSS vulnerabilities.
- Ehanced supported for nested serialization formats.
- Major rework for scan scheduling engine for increased scalability.

## June 2018
- New backend scanning engine with beta support for SQL injection and XXE
- Adding beta support for crawling of HTML content.

## May 2018
- Bumping free scanner coverage limit from 100 to 300.
- New detector for encrypted IPA.
- Fix false positive in dynamic rules detecting weak encryption.

## April 2018
- Porting LLDB for iOS to work on Linux.
- New backend scan engine.
- New experimental crawler.

## February 2018
- Adding Support for authenticated scan.
- Final version of Java hook engine with stack trace support and full context inspection.
- Major enhancement to the taint engine reducing false positives.
- Multiple bug fixes affecting PDF generation and false positive declaration.
- Adding feature to report false positives and remove them from the final report.
- Multiple new dynamic rules to trace sensitive function call.
- New agent to detect sensitive material files, like private encryption keys.

## January 2018
- Surface static taint analysis coverage in the scan report.

## December 2017
- Unsafe Transport App Security settings in iOS apps are reported as vulnerabilities.
- Performance enhancement for the support of large multidex files.
- Bug fix in method xref for multidex files.
- Enhance vulnerability de-duplication.
- Multiple bug fixes for iOS scan rules.

## November 2017
- Advanced option to detect weak files permission for both Android and iOS. (OWASP Mobile Top 10 - M2)
- Advanced option to detect Personal Identifiable Information (PII) leakage for both Android and iOS. (OWASP Mobile Top 10 - M2)
- Advanced option to detect clear-text traffic for both Android and iOS. (OWASP Mobile Top 10 - M3)
- Advanced option to detect insecure TLS/SSL validation for both Android and iOS. (OWASP Mobile Top 10 - M3)
- Advanced option to support iOS call to weak Cryptographic API. (OWASP Mobile Top 10 - M5)
- Advanced option to support download PDF report.

## September 2017
- Stabilizing unlimited scan feature with bug fixes.
- Correction of false positives in Insecure Encryption Mode.
- Correction of false positives in ASLR detection for iOS Apps.
- Move to a clustered architecture to support increase scan load.
- Final version to support dedicated unlimited scans.

## August 2017
- New feature to support dedicated scans.
- Tweaks and updates to the user interface to support fast uploading.

## July 2017
- New backend system to support the increased load.
- Major code refactoring of all agents to support the new backend system.
- Multiple bug fixes.

## June 2017
- New static taint engine for Android Bytecode.
- Multiple bug fixes and performance tweaks.
