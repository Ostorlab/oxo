# Compliance for Mobile Devices

## GDPR

### What is it ?
General Data Protection Regulation : is the most important change in data privacy regulation in 20 years. This regulation replaces the Data Protection Directive of 1995. It is designed to harmonize data privacy across the EU, protect all EU citizens data privacy and reshape the way companies and organizations approach data privacy.

Businesses that fail to comply can be fined up to 20 million euros, or 4% of their annual global turnover.

GDPR aims to protect user data storage and usage and to ensure that the user is in control of its data.
 
The GDPR applies to all businesses with customers websites or mobile visitors who are from the European Union. This means that any organization in the world that works with EU residents personal data in any manner has obligations to protect that users data and be GDPR compliant. 

Let's first go over a few key definitions. 

The first one is **data controller**: a data controller is the entity that determines the purpose for and means of collecting and processing personal data. If you own a website or mobile app and you're deciding what is collected, how it's collected and for what purpose, then you are a data controller.

The second term is **data processor**: a data processor is an organization that processes personal data on behalf of the data collector. For example this can be a third party service that is plugged into your website or app. This can be an analytics tool such as Google Analytics or it can be a cloud service such as Amazon Web Services that has access to, or hosts your customers data.
 
The third term is **data subject**: a data subject is a person whose data is processed. For example an app user or a website visitor.
 
Now that we've gone over these terms let's get into the meat of what a general data protection regulation is.
 
Personal data under the GDPR includes any information relating to an identifiable person who can be identified in reference to any sort of identifier for your website or apps. 

### How to become GDPR compliant?  
The ten things you should consider in order to have a GDPR compliant mobile app:
 
#### Privacy by Design
Privacy by design is now a legal requirement under the GDPR. From the moment you start creating your mobile app you should be considering your users privacy. According to GDPR article 23 your app must only hold and process user data that is absolutely necessary. Think about your user data from the very start and don't let it be an afterthought. As well as this you should encrypt whatever personal data you collect with a strong encryption algorithm this will help minimize the impact of a data breach 
#### Ask for Explicit Consent
Under the GDPR, businesses must request and receive user consent in order to collect, use and move personal data. This includes data collected for advertising, analytics, crash logging or anything else. The opt-in must be understandable and clear because you won't be able to get away with any confusing terms and conditions that no one is likely to read or fully understand. It is highly recommended to show a consent screen on app launch as this is the only way to be fully GDPR compliant. You should also notify users on these screens when their data will be used. Also your users must be able to withdraw consent as easily as it was for them to give it, so you might need to create another page on your website to allow your users to opt out.
#### Provide Visibility and Transparency
One of the most important aspects of GDPR is how the data you collect is actually used. If your data controller needs to be aware of how your users can effectively manage and protect their user data providing visibility and transparency through a clear and understandable privacy policy not only benefits the users of your mobile app but it is also a requirement of the App Store. Google will actually remove your app if they can't find a privacy policy on your Play Stores profile page and accessible inside your app. You may choose to have a sidebar or menu item that links to these legal terms of your mobile app. This will enable users to easily find, read and understand how your mobile app or any external services are using their data.
#### Respond to user requests
If someone asks how you are using their data, under GDPR you are legally obligated to respond to them. This is called a subject access request. When a user asks for information about their data or a copy of the data that is used in your mobile app you have one month to respond. For more complicated requests you have up to three months to respond. Our recommendation is just to create a page on your website and mobile app that includes your business contact information. This will allow users to contact you easily.
#### The Right to be Forgotten
Article 17 of the GDPR highlights the right to erasure or the right to be forgotten. This means that when a user asks you to remove your data acquired through your website or mobile app you are obligated to remove every personal detail you hold on them. Take this request seriously and comply with the request on every system you control. You must remove data whether you control it directly or through tools such as Google Analytics 
#### Review Services and SDKs you use
If your app sends personal data to an external service for processing -e.g.  an app that analyzes app usage- then you need to be clear and transparent about where that is and who will be in control of the transferred data. You should sign a data processing agreement with your data processors as it is a general requirement under the GDPR. But don't assume that all the third parties and SDKs connected to your app are GDPR compliant. If there is a data breach on one of your third parties, that leads to your user data being exposed then you are responsible therefore you should only have contracts with providers who can provide sufficient guarantees that GDPR requirements will be met and your user's data will be sufficiently protected
#### Data Breach Notifications
The GDPR is forcing tighter deadlines for businesses to notify the National Supervisory Authorities and their users. Disclosure must now happen within the first 72 hours, so make sure you establish a clear step-by-step process that you can follow in case of a breach. Now this includes how you will inform your users and the National Supervisory Authorities of the breach. You may need to invest in a technology that notifies you when a risk is present and ensures that you have continuous surveillance of your data.
#### Appointing a Data Protection Officer
Your company may need to appoint a Data Protection Officer in order to be GDPR compliant. This applies to you if:
    
    - You are a public authority, except for courts acting in their judicial capacity 
    - Your core activities require a large-scale, regular and systematic monitoring of individuals such as online behavior tracking 
    - Your core activities consist of large-scale processing of special categories of data, or data relating to criminal convictions and offenses
Assess whether or not your business needs a DPO in order to be compliant. If so, you should appoint one, and inform your website or mobile app users on how they can contact your DPO. 
#### Encryption and Data Storage
Ensure that your app uses SSL/TLS and HTTPS for external communications. While communicating personal information of any kind your data must be encrypted. Not encrypting data means that the information set will be in clear text and will be exposed over the Internet. 
#### Log and Justify your data collection
Article 30 of the GDPR outlines that each controller, or representative of the controller “shall maintain a record of processing activities under its responsibility”. That means, in order to ensure your GDPR compliance you should start documenting all the data that either you collect yourself or through a third-party. 

## PCI DSS
 
### What is the PCI DSS ?
The Payment Card Industry Data Security Standard or PCI DSS was developed to encourage and enhance cardholder data security and to facilitate the broad adoption of consistent data security measures globally. 
It applies to all merchants and service providers that process, transmit or store cardholder data. If your organization handles card payments, it must comply- or risk suffering financial penalties or even the withdrawal of the facility to accept card payments. 
The PCI DSS was launched in 2004 and is the result of collaboration between the major credit card brands: American Express, Discover, JCB, MasterCard and Visa.

### Do I need to comply with the PCI DSS ? 
All organizations that accept credit and debit cards or that store, process and/or transmit cardholder data need to comply with the standard. Merchants and service providers compliance
requirements differ depending on a number of factors including the size of the organization and the volume of transactions it undertakes. 

### What are the penalties for non-compliance ?
The PCI DSS is a standard not of law. It's enforced through contracts between merchants acquiring banks and payment brands. Each payment brand can fine acquiring banks for PCI DSS compliance violations, and acquiring banks can withdraw the ability to accept card payments from non-compliant merchants.
It's also worth remembering that a PCI DSS breach is always a GDPR breach as
cardholder data is classified as personal data under the regulation. 
So as well as any enforcement action from your acquiring bank, your organization could face administrative fines of up to 20 million Euros or 4% of annual global turnover (whichever is greater) under the GDPR.

### How to become PCI DSS compliant? 
The PCI DSS specifies 12 requirements that are organized into 6 controlled objectives:
 
    1. Build and maintain a secure network:
        - Install and maintain a firewall configuration to protect cardholder data 
        - Do not use vendor-supplied defaults for system passwords and other security parameters
    2. Protect cardholder data: 
        - Protect stored cardholder data 
        - Encrypt transmission of cardholder data across open public networks 
    3. Maintain a vulnerability management programme: 
        - Use and regularly update antivirus software or programs 
        - Develop and maintain secure systems and applications 
    4. Implement strong access control measures:
        - Restrict access to cardholder data by business need-to-know 
        - Assign a unique ID to each person with computer access 
        - Restrict physical access to cardholder data 
    5. Regularly monitor and test networks:
        - Track and monitor all access to network resources and cardholder data 
        - Regularly test security systems and processes 
    6. Maintain an information security policy:
        - Maintain a policy that addresses information security for employees and contractors 


## PSD2

### What is it ?
Revised Payment Services Directive 2 : is the new European regulation for electronic payment services which replaced the Payment Services Directive. It progressively began entering into force between January 13, 2018 and September 14, 2019 and drives fundamental changes in the industry as it gives non-banking third party players access to bank infrastructure 

### It’s purpose ?
PSD2 seeks to improve consumer protection, boost competition and innovation and reinforce security in the payments market. 

#### Biggest changes ?
An important element of PSD2 is the requirement for Strong Customer Authentication (SCA). 
It involves the use of two authentication factors for bank operations including payments and access to accounts online or via apps.


## HIPAA

### What is it ?
Health Insurance Portability and Accountability Act, commonly referred to as HIPAA sets
forth policies that protect the way patients' medical information are stored and shared. 
Federal law requires your medical practice to be HIPAA compliant; this means that the way you protect patients medical records and other information adheres to HIPAA standards.

### How to become HIPAA compliant ?
In order to be HIPAA compliant you must:

    - Analyze the vulnerability of patients electronic medical records that are stored at your office or off-site 
    - Make sure that all protected health information (PHI) is encrypted 
    - Create and implement policies to address PHI that has been compromised, stolen or misplaced 
    - Only work with partners and vendors that can assure the security of your patient's information 
    - Give patients electronic access to their medical records within 30 days of any request
    - Protect patient information from insurance providers if procedures are paid for out of pocket 
    - Share your full privacy policy with patients via individual communications and by publicly posting the policy on your website 
    
## NBD

### What is the Notifiable Data Breaches scheme?
The amendment to the Australian Privacy Act established the Notifiable Data Breaches scheme in Australia, and became effective from the 22nd of February 2018.
The NDB scheme strengthens protections to personal information, providing affected individuals with an opportunity to take steps to protect their personal information following a data breach.
The consequences of failing to notify or not complying with the scheme attract a maximum penalty of up to $360,000 for individuals and $1,800,000 for corporations.

####Who must comply with the notifiable data breach scheme?
The following entities must comply with the scheme:

    1. Australian government agencies
    2. All businesses and not-for-profit organisations with an annual turnover of 3 million dollars or more
    3. Small businesses including:
        - All private sector health providers
        - Those that trade in personal information
        - Companies that use tax file numbers, however if the annual turnover is below 3 million dollars the NDB scheme will apply only in relation to tax file number information
        - Those that hold personal information in relation to certain activities, for example providing services to the Commonwealth under a contract

### What is an eligible data breach under the scheme?
An eligible data breach arises when the following three criteria are satisfied:

    1. There is unauthorized access to or disclosure of personal information or a loss of personal information that an organization holds
    2. This is likely to result in serious harm to one or more individuals
    3. The organization has not been able to prevent the likely risk of serious harm with remedial action

### What is a data breach?
#### Unauthorized access: 
This occurs when personal information is accessed by someone who is unauthorized to do so
#### Unauthorized disclosure: 
This occurs when an organization whether intentionally or unintentionally makes personal information accessible or visible to others outside the organization and releases that information from its effective control in a way that is not permitted by the Privacy Act
#### Loss of information: 
This refers to the accidental or inadvertent loss of personal information held by an organization where it is likely to result in unauthorized access or disclosure

### What types of data are involved in a data breach?
There are some kinds of personal information that may be more likely to cause an individual serious harm if compromised:

    - Sensitive information, such as information about an individual's health
    - Documents commonly used for identity fraud, including a driver's license and passport details...
    - Financial information

### When should you notify?
A notifiable breach event happens when the following criteria is met:

    - A data breach occurred
    - The breach will likely result in serious harm
    - The organization holding this information was not able to prevent the risk of serious harm
    
### Who should you notify?
You must notify any individuals that are at risk of serious harm as a result of the data breach.
You must also notify the Australian Information Commissioner.
There are three options for notifying affected individuals:

    1. Notify all individuals whose personal information is involved in the eligible data breach
    2. Notify only the individuals who are at likely risk of serious harm
    3. Publish your notification and publicize it with the aim of bringing it to the attention of all individuals at likely risk of serious harm

### How to notify affected individuals in the Office of the Australian Information Commissioner (OAIC)?
Your notification and statement to the OAIC must include the following information:

    - The identity in contact details of your agency your organisation
    - A description of the eligible data breach
    - The kinds of information involved in the eligible data breach
    - What steps your agency or organization recommends that individuals take in response to the eligible data breach


### When to conduct an assessment?
If you suspect a data breach which may meet the threshold of “likely to result in serious harm” then you must conduct an assessment.

Generally there is a maximum of 30 days to conduct this assessment. This begins from when you become aware of a potential breach.

You should review your data breach response framework to ensure that relevant personnel will be made aware of a breach as soon as possible.

It is not expected that every data breach will require an assessment that takes 30 days to complete before notification occurs. You must notify as soon as possible once you hold the belief an eligible data breach has occurred.

### What is involved in an assessment?
The Act says assessments must be reasonable and expeditious. It is up to entities to decide what process to follow when conducting an assessment. Generally an assessment should cover off the following three stages:

    1. Initiate: decide whether an assessment is necessary, and identify which person or group will be responsible for completing it
    2. Investigate: quickly gather relevant information about the suspected breach including for example what personal information is affected, who may have had access to the information and the likely impacts
    3. Evaluate: make a decision based on the investigation about whether the identified breach is an eligible data breach
    
## NERC

### What is it ?
The North American Electric Reliability Corporation Critical Infrastructure Protection (NERC CIP) standards are specific guidelines to the power industry. It aims to ensure reliability and security standards for BES (Bulk Electric System). As mobile devices are more and more used to service these infrastructures, it became a priority to implement mobile security solutions in order to prevent device, network and app attacks.  

### Who must comply ?
All bulk power system owners, operators, and users must comply with NERC-approved Reliability Standards. These entities are required to register with NERC through the appropriate Regional Entity.

## NIST
### What is it ?
The National Institute of Standards and Technology is a non-regulatory federal agency within the U.S. Department of Commerce. Companies that provide products and services to the federal government need to meet certain security mandates set by NIST.

### It’s purpose ?
The stated goal of the NIST report is that mobile devices need to achieve three primary security goals:

    1. Confidentiality: any transmitted or stored data must be protected against unauthorized third-parties
    2. Integrity: any transmitted or stored data need to be confirmed as uncorrupted
    3. Availability: although devices must be protected, they also need to be functional and allow right users to access company resources 

NIST recommendations to strengthen mobile cybersecurity:

    - Install a mobile device security policy: the more consistent this policy is with existing security policy for non-mobile systems, the better
    - Develop System Threat Models for mobile devices: mobile devices are more highly exposed to threats due to their portability. Public/unprotected Wi-Fi, third-party applications, malware and adware are all potential means for attacks. By developing a system of threat models, most likely threats vulnerabilities can be highlighted 
    - Ensure that company-issued devices are fully secure
