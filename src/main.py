import os
import pandas as pd
import numpy as np
import random
import re
import os
import argparse
import torch
import torch.nn as nn
from model.Conv2D_Conv1D_LSTM.Conv2D_Conv1D_LSTM import Conv2D_Conv1D_LSTM
from utils.data_generator_ArCSL import *

def main(args):
    seed = 42

    random.seed(seed)
    torch.manual_seed(seed)
    np.random.seed(seed)

    if args.device == 'mps':
        torch.mps.manual_seed(seed)
        torch.backends.mps.deterministic=True
        torch.backends.mps.benchmark = False
    elif args.device == 'cuda':
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic=True
        torch.backends.cudnn.benchmark = False

    gloss_dict = get_gloss_dict(args.data_path)
    gloss_dict["-"] = 0

    model = None
    if args.model == "Conv2D_Conv1D_LSTM":
        model = Conv2D_Conv1D_LSTM(num_classes=len(gloss_dict.keys()), hidden_size=512).to(args.device)

    if args.phase == "train":
        train(model, args)

    if args.phase == "eval":
        eval(model, args)


def train(model, args):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001, weight_decay=0.0001)
    ctc_loss = nn.CTCLoss(reduction='mean', zero_infinity=False, blank=0)

    for epoch in range(args.epochs):
        data_gen = data_generator_ArCSL(args.data_path, batch_size=args.batch_size)
        num_batches = total_vids_len(args.phase)//args.batch_size
        
        training_loss = 0
        for batch in tqdm(data_gen, desc=f"Epoch: {epoch+1}", total=num_batches):
            frames = batch['frames']
            y = batch['y']
            
            optimizer.zero_grad()
            out = model(frames, args.device)
            out = out.permute(1, 0, 2).to("cpu")

            output_lengths = torch.full((out.shape[1],), out.shape[0], dtype=torch.long).to("cpu")
            target_lengths = torch.tensor([len(i) for i in y]).to("cpu")
            flattenned_y = torch.tensor([item for sublist in y for item in sublist]).to("cpu")

            loss = ctc_loss(out, flattenned_y, output_lengths, target_lengths)

            loss.backward()
            optimizer.step()

            training_loss += loss.item()
        
        print(f"Epoch: {epoch+1}, Loss: {training_loss}")
        print()

def eval(model, args):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', dest='data_path')
    parser.add_argument('--model', dest='model', default="Conv2D_Conv1D_LSTM")
    parser.add_argument('--device',dest='device', default='cuda')
    parser.add_argument('--epochs',dest='epochs', default=50)
    parser.add_argument('--batch_size',dest='batch_size', default=2)
    parser.add_argument('--phase',dest='phase', default="train")
    args = parser.parse_args()

    main(args)