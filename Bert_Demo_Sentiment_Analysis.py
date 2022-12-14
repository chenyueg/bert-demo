# -*- coding: utf-8 -*-
"""Bert Demo - Sentiment Analysis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18KIvrNyG0Lwfq6u8y4IYN1umb-Ys43gl

# 1. Activate GPU and Install Dependencies
"""

# Activate GPU for faster training by clicking on 'Runtime' > 'Change runtime type' and then selecting GPU as the Hardware accelerator
# Then check if GPU is available
import torch
torch.cuda.is_available()

# Install required libraries
!pip install datasets transformers huggingface_hub
!apt-get install git-lfs

"""#2. Preprocess data"""

# Load data
from datasets import load_dataset
imdb = load_dataset("imdb")

# Create a smaller training dataset for faster training times
small_train_dataset = imdb["train"].shuffle(seed=42).select([i for i in list(range(300))])
small_test_dataset = imdb["test"].shuffle(seed=42).select([i for i in list(range(300))])
print(small_train_dataset[0])
print(small_test_dataset[0])

# Set DistilBERT tokenizer
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

# Prepare the text inputs for the model
def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True)

tokenized_train = small_train_dataset.map(preprocess_function, batched=True)
tokenized_test = small_test_dataset.map(preprocess_function, batched=True)

# Use data_collator to convert our samples to PyTorch tensors and concatenate them with the correct amount of padding
from transformers import DataCollatorWithPadding
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

"""# 3. Training the model"""

# Define DistilBERT as our base model:
from transformers import AutoModelForSequenceClassification
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)

# Define the evaluation metrics 
import numpy as np
from datasets import load_metric

def compute_metrics(eval_pred):
    load_accuracy = load_metric("accuracy")
    load_f1 = load_metric("f1")
    
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    accuracy = load_accuracy.compute(predictions=predictions, references=labels)["accuracy"]
    f1 = load_f1.compute(predictions=predictions, references=labels)["f1"]
    return {"accuracy": accuracy, "f1": f1}

# Log in to your Hugging Face account 
# Get your API token here https://huggingface.co/settings/token
from huggingface_hub import notebook_login

notebook_login()

# Define a new Trainer with all the objects we constructed so far
from transformers import TrainingArguments, Trainer

repo_name = "finetuning-sentiment-model-3000-samples"

training_args = TrainingArguments(
    output_dir=repo_name,
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=2,
    weight_decay=0.01,
    save_strategy="epoch", 
    push_to_hub=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_test,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# Train the model
trainer.train()

# Compute the evaluation metrics
trainer.evaluate()

"""# 4. Analyzing new data with the model"""

# Upload the model to the Hub
trainer.push_to_hub()

# Run inferences with your new model using Pipeline
from transformers import pipeline

sentiment_model = pipeline(model="chenyueg/finetuning-sentiment-model-3000-samples")

sentiment_model(["I love this move", "This movie sucks!"])