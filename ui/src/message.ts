interface Failure {
    schema: "failure";
    explanation: string;
}

interface Nothing {
    schema: "nothing";
}

interface PlainText {
    schema: "text";
    value: string;
}

interface Other {
    schema: "other";
    description: string;
}

interface Script {
    schema: "script";
    code: string;
    language: string;
    source_file: string;
}

interface Command {
    schema: "command";
    command: string;
}

type Message = 
    | Nothing 
    | Failure 
    | PlainText 
    | Script
    | Command
    | Other;
